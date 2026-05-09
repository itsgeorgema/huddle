import time
from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agents.claim_extraction_agent import ClaimExtractionAgent
from app.agents.conflict_classifier_agent import ConflictClassifierAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.mediation_agent import PreMediationAgent
from app.agents.participant_profiler_agent import ParticipantProfilerAgent
from app.agents.summarizer_agent import ConsensusSummarizerAgent
from app.db.models import (
    AgentRun,
    Claim,
    ConflictEdge,
    DeliberationGroup,
    GroupMember,
    MediationBrief,
    Participant,
    ParticipantProfile,
    SessionModel,
    Statement,
)
from app.services.embedding_service import EmbeddingService
from app.services.graph_service import ConflictGraphService
from app.services.observability import AGENT_FAILURES, AGENT_LATENCY, PIPELINE_RUNS
from app.services.routing_engine import RoutingEngine
from app.services.scoring_service import ScoringService


class AgentOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding = EmbeddingService()
        self.scoring = ScoringService()
        self.router = RoutingEngine()
        self.graphs = ConflictGraphService()

    async def run(self, session_id: str, mode: str = "mock", group_size: int = 4, constraints: dict | None = None) -> dict:
        constraints = constraints or {}
        started = time.perf_counter()
        session = self.db.get(SessionModel, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.status = "running"
        self.db.commit()
        self._clear_previous_outputs(session_id)

        try:
            participants = self._participant_dicts(session_id)
            raw_statements = self._statement_dicts(session_id)
            intake = await self._run_agent(session_id, IntakeAgent(), {"statements": raw_statements})
            self._update_statement_intake(intake["statements"])

            claims_out = await self._run_agent(session_id, ClaimExtractionAgent(), {"statements": intake["statements"]})
            claims = self._persist_claims(session_id, claims_out["claims"])

            conflicts_out = await self._run_agent(session_id, ConflictClassifierAgent(), {"claims": claims})
            conflict_edges = self._persist_conflicts(session_id, conflicts_out["conflict_edges"])

            profiles_out = await self._run_agent(
                session_id,
                ParticipantProfilerAgent(),
                {"claims": claims, "conflict_edges": conflict_edges},
            )
            profiles = self._persist_profiles(session_id, profiles_out["profiles"])

            claim_to_participant = {claim["claim_id"]: claim["participant_id"] for claim in claims}
            pairwise = self.scoring.pairwise_risk(
                [participant["id"] for participant in participants],
                claim_to_participant,
                conflict_edges,
            )
            groups = self.router.route(participants, profiles, pairwise, group_size, constraints)
            persisted_groups = self._persist_groups(session_id, groups)

            claims_by_participant: dict[str, list[dict]] = defaultdict(list)
            for claim in claims:
                claims_by_participant[claim["participant_id"]].append(claim)
            briefs_out = await self._run_agent(
                session_id,
                PreMediationAgent(),
                {"groups": persisted_groups, "claims_by_participant": claims_by_participant},
            )
            self._persist_briefs(session_id, briefs_out["briefs"])

            summary = await self._run_agent(
                session_id,
                ConsensusSummarizerAgent(),
                {"claims": claims, "conflict_edges": conflict_edges},
            )
            session.status = "complete"
            self.db.commit()
            PIPELINE_RUNS.labels(mode=mode, status="complete").inc()
            return {
                "session_id": session_id,
                "status": "complete",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "claims": len(claims),
                "conflict_edges": len(conflict_edges),
                "groups": len(persisted_groups),
                "pairwise_risk": pairwise,
                "summary": summary,
            }
        except Exception:
            self.db.rollback()
            session = self.db.get(SessionModel, session_id)
            session.status = "failed"
            self.db.commit()
            PIPELINE_RUNS.labels(mode=mode, status="failed").inc()
            raise

    def _clear_previous_outputs(self, session_id: str) -> None:
        group_ids = [row[0] for row in self.db.execute(select(DeliberationGroup.id).where(DeliberationGroup.session_id == session_id))]
        for model in [MediationBrief, GroupMember]:
            if group_ids:
                self.db.execute(delete(model).where(model.group_id.in_(group_ids)))
        for model in [DeliberationGroup, ParticipantProfile, ConflictEdge, Claim]:
            self.db.execute(delete(model).where(model.session_id == session_id))
        self.db.commit()

    async def _run_agent(self, session_id: str, agent, payload: dict) -> dict:
        run = AgentRun(session_id=session_id, agent_name=agent.name, status="running", input_json=payload)
        self.db.add(run)
        self.db.commit()
        try:
            output, latency = await agent.run_with_timing(payload)
            run.status = "complete"
            run.output_json = output
            run.latency_ms = latency
            AGENT_LATENCY.labels(agent=agent.name).observe(latency)
            self.db.commit()
            return output
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            AGENT_FAILURES.labels(agent=agent.name).inc()
            self.db.commit()
            raise

    def _participant_dicts(self, session_id: str) -> list[dict]:
        rows = self.db.scalars(select(Participant).where(Participant.session_id == session_id)).all()
        return [{"id": row.id, "display_name": row.display_name} for row in rows]

    def _statement_dicts(self, session_id: str) -> list[dict]:
        rows = self.db.scalars(select(Statement).where(Statement.session_id == session_id)).all()
        return [{"id": row.id, "participant_id": row.participant_id, "text": row.text} for row in rows]

    def _update_statement_intake(self, statements: list[dict]) -> None:
        for item in statements:
            row = self.db.get(Statement, item["statement_id"])
            row.cleaned_text = item["cleaned_statement"]
            row.detected_tone = item["detected_tone"]
            row.language = item["language"]
        self.db.commit()

    def _persist_claims(self, session_id: str, claims: list[dict]) -> list[dict]:
        persisted = []
        for claim in claims:
            namespaced_claim = {**claim, "claim_id": f"{session_id}:{claim['claim_id']}"}
            db_claim = Claim(
                id=namespaced_claim["claim_id"],
                session_id=session_id,
                participant_id=claim["participant_id"],
                statement_id=claim["statement_id"],
                text=claim["text"],
                claim_type=claim["claim_type"],
                stakeholder=claim["stakeholder"],
                value_label=claim["value"],
                confidence=claim["confidence"],
                embedding=self.embedding.embed(claim["text"]),
            )
            self.db.add(db_claim)
            persisted.append(namespaced_claim)
        self.db.commit()
        return persisted

    def _persist_conflicts(self, session_id: str, edges: list[dict]) -> list[dict]:
        for edge in edges:
            self.db.add(
                ConflictEdge(
                    session_id=session_id,
                    source_claim_id=edge["source_claim"],
                    target_claim_id=edge["target_claim"],
                    edge_type=edge["edge_type"],
                    conflict_type=edge["conflict_type"],
                    risk_score=edge["risk_score"],
                    reason=edge["reason"],
                )
            )
        self.db.commit()
        return edges

    def _persist_profiles(self, session_id: str, profiles: list[dict]) -> list[dict]:
        for profile in profiles:
            self.db.add(
                ParticipantProfile(
                    session_id=session_id,
                    participant_id=profile["participant_id"],
                    viewpoint_cluster=profile["viewpoint_cluster"],
                    main_values=profile["main_values"],
                    bridge_score=profile["bridge_potential"],
                    conflict_risk=profile["conflict_risk"],
                )
            )
        self.db.commit()
        return profiles

    def _persist_groups(self, session_id: str, groups: list[dict]) -> list[dict]:
        persisted = []
        for group in groups:
            db_group = DeliberationGroup(
                session_id=session_id,
                label=group["label"],
                risk_score=group["risk_score"],
                diversity_score=group["diversity_score"],
                bridge_score=group["bridge_score"],
                reasoning=group["reasoning"],
            )
            self.db.add(db_group)
            self.db.flush()
            for participant_id in group["participant_ids"]:
                self.db.add(GroupMember(group_id=db_group.id, participant_id=participant_id))
            persisted.append({**group, "id": db_group.id})
        self.db.commit()
        return persisted

    def _persist_briefs(self, session_id: str, briefs: list[dict]) -> None:
        for brief in briefs:
            self.db.add(
                MediationBrief(
                    session_id=session_id,
                    group_id=brief["group_id"],
                    shared_ground=brief["shared_ground"],
                    likely_tensions=brief["likely_tensions"],
                    bridge_questions=brief["bridge_questions"],
                    discussion_order=brief["discussion_order"],
                )
            )
        self.db.commit()
