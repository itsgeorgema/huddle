import time
from collections import defaultdict
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agents.claim_extraction_agent import ClaimExtractionAgent
from app.agents.conflict_classifier_agent import ConflictClassifierAgent
from app.agents.diversity_load_balancer_agent import DiversityLoadBalancerAgent
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
from app.services.observability import AGENT_FAILURES, AGENT_LATENCY, PIPELINE_RUNS


class DeliberationState(TypedDict, total=False):
    session_id: str
    group_size: int
    constraints: dict[str, Any]
    participants: list[dict[str, Any]]
    raw_statements: list[dict[str, Any]]
    intake: dict[str, Any]
    claims: list[dict[str, Any]]
    conflict_edges: list[dict[str, Any]]
    profiles: list[dict[str, Any]]
    pairwise_risk: dict[str, Any]
    groups: list[dict[str, Any]]
    persisted_groups: list[dict[str, Any]]
    routing_policy: dict[str, Any]
    briefs: dict[str, Any]
    summary: dict[str, Any]


class AgentOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding = EmbeddingService()
        self.pipeline = self._compile_langgraph()

    async def run(self, session_id: str, group_size: int = 4, constraints: dict | None = None) -> dict:
        constraints = constraints or {}
        started = time.perf_counter()
        session = self.db.get(SessionModel, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.status = "running"
        self.db.commit()
        self._clear_previous_outputs(session_id)

        try:
            final_state = await self.pipeline.ainvoke(
                {
                    "session_id": session_id,
                    "group_size": group_size,
                    "constraints": constraints,
                    "participants": self._participant_dicts(session_id),
                    "raw_statements": self._statement_dicts(session_id),
                }
            )
            session.status = "complete"
            self.db.commit()
            PIPELINE_RUNS.labels(status="complete").inc()
            return {
                "session_id": session_id,
                "status": "complete",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "claims": len(final_state["claims"]),
                "conflict_edges": len(final_state["conflict_edges"]),
                "groups": len(final_state["persisted_groups"]),
                "pairwise_risk": final_state["pairwise_risk"],
                "routing_policy": final_state["routing_policy"],
                "summary": final_state["summary"],
            }
        except Exception:
            self.db.rollback()
            session = self.db.get(SessionModel, session_id)
            session.status = "failed"
            self.db.commit()
            PIPELINE_RUNS.labels(status="failed").inc()
            raise

    def _compile_langgraph(self):
        graph = StateGraph(DeliberationState)
        graph.add_node("intake", self._intake_node)
        graph.add_node("claim_extraction", self._claim_extraction_node)
        graph.add_node("conflict_classification", self._conflict_classification_node)
        graph.add_node("participant_profiling", self._participant_profiling_node)
        graph.add_node("diversity_load_balancing", self._diversity_load_balancing_node)
        graph.add_node("pre_mediation", self._pre_mediation_node)
        graph.add_node("consensus_summary", self._summary_node)
        graph.set_entry_point("intake")
        graph.add_edge("intake", "claim_extraction")
        graph.add_edge("claim_extraction", "conflict_classification")
        graph.add_edge("conflict_classification", "participant_profiling")
        graph.add_edge("participant_profiling", "diversity_load_balancing")
        graph.add_edge("diversity_load_balancing", "pre_mediation")
        graph.add_edge("pre_mediation", "consensus_summary")
        graph.add_edge("consensus_summary", END)
        return graph.compile()

    async def _intake_node(self, state: DeliberationState) -> DeliberationState:
        intake = await self._run_agent(
            state["session_id"],
            IntakeAgent(),
            {"statements": state["raw_statements"]},
        )
        self._update_statement_intake(intake["statements"])
        return {"intake": intake}

    async def _claim_extraction_node(self, state: DeliberationState) -> DeliberationState:
        output = await self._run_agent(
            state["session_id"],
            ClaimExtractionAgent(),
            {"statements": state["intake"]["statements"]},
        )
        return {"claims": await self._persist_claims(state["session_id"], output["claims"])}

    async def _conflict_classification_node(self, state: DeliberationState) -> DeliberationState:
        output = await self._run_agent(
            state["session_id"],
            ConflictClassifierAgent(),
            {"claims": state["claims"]},
        )
        return {"conflict_edges": self._persist_conflicts(state["session_id"], output["conflict_edges"])}

    async def _participant_profiling_node(self, state: DeliberationState) -> DeliberationState:
        output = await self._run_agent(
            state["session_id"],
            ParticipantProfilerAgent(),
            {"claims": state["claims"], "conflict_edges": state["conflict_edges"]},
        )
        return {"profiles": self._persist_profiles(state["session_id"], output["profiles"])}

    async def _diversity_load_balancing_node(self, state: DeliberationState) -> DeliberationState:
        output = await self._run_agent(
            state["session_id"],
            DiversityLoadBalancerAgent(),
            {
                "participants": state["participants"],
                "profiles": state["profiles"],
                "claims": state["claims"],
                "conflict_edges": state["conflict_edges"],
                "group_size": state["group_size"],
                "constraints": state["constraints"],
            },
        )
        persisted_groups = self._persist_groups(state["session_id"], output["groups"])
        return {
            "groups": output["groups"],
            "persisted_groups": persisted_groups,
            "pairwise_risk": output["pairwise_risk"],
            "routing_policy": output["routing_policy"],
        }

    async def _pre_mediation_node(self, state: DeliberationState) -> DeliberationState:
        claims_by_participant: dict[str, list[dict]] = defaultdict(list)
        for claim in state["claims"]:
            claims_by_participant[claim["participant_id"]].append(claim)
        output = await self._run_agent(
            state["session_id"],
            PreMediationAgent(),
            {"groups": state["persisted_groups"], "claims_by_participant": claims_by_participant},
        )
        self._persist_briefs(state["session_id"], output["briefs"])
        return {"briefs": output}

    async def _summary_node(self, state: DeliberationState) -> DeliberationState:
        summary = await self._run_agent(
            state["session_id"],
            ConsensusSummarizerAgent(),
            {"claims": state["claims"], "conflict_edges": state["conflict_edges"]},
        )
        return {"summary": summary}

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
            if row:
                row.cleaned_text = item.get("cleaned_statement", row.text)
                row.detected_tone = item.get("detected_tone", "neutral")
                row.language = item.get("language", "en")
        self.db.commit()

    async def _persist_claims(self, session_id: str, claims: list[dict]) -> list[dict]:
        texts = [claim["text"] for claim in claims]
        try:
            embeddings = await self.embedding.embed_batch(texts)
        except Exception:
            embeddings = [[0.0] * self.embedding.dimensions] * len(claims)

        persisted = []
        for claim, embedding in zip(claims, embeddings):
            namespaced_claim = {**claim, "claim_id": f"{session_id}:{claim['claim_id']}"}
            db_claim = Claim(
                id=namespaced_claim["claim_id"],
                session_id=session_id,
                participant_id=claim["participant_id"],
                statement_id=claim["statement_id"],
                text=claim["text"],
                claim_type=claim.get("claim_type", "concern"),
                stakeholder=claim.get("stakeholder", "residents"),
                value_label=claim.get("value", "community benefit"),
                confidence=claim.get("confidence", 0.75),
                embedding=embedding,
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
                    edge_type=edge.get("edge_type", "conflicts_with"),
                    conflict_type=edge.get("conflict_type", "value_conflict"),
                    risk_score=edge.get("risk_score", 0.5),
                    reason=edge.get("reason", ""),
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
                    viewpoint_cluster=profile.get("viewpoint_cluster", "unclassified"),
                    main_values=profile.get("main_values", []),
                    bridge_score=profile.get("bridge_potential", 0.0),
                    conflict_risk=profile.get("conflict_risk", 0.0),
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
                risk_score=group.get("risk_score", 0.0),
                diversity_score=group.get("diversity_score", 0.0),
                bridge_score=group.get("bridge_score", 0.0),
                reasoning=group.get("reasoning", ""),
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
                    shared_ground=brief.get("shared_ground", []),
                    likely_tensions=brief.get("likely_tensions", []),
                    bridge_questions=brief.get("bridge_questions", []),
                    discussion_order=brief.get("discussion_order", []),
                )
            )
        self.db.commit()
