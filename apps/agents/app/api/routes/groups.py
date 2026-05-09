from itertools import combinations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.mediation import GroupRead, LiveIntervention, LiveMessage, MediationBriefRead
from app.agents.mediation_agent import LiveMediationAgent
from app.db.models import (
    Claim,
    ConflictEdge,
    DeliberationGroup,
    GroupMember,
    MediationBrief,
    Participant,
)
from app.db.session import get_db

router = APIRouter(prefix="/sessions/{session_id}", tags=["groups"])


@router.get("/groups", response_model=list[GroupRead])
def groups(session_id: str, db: Session = Depends(get_db)) -> list[GroupRead]:
    rows = db.scalars(select(DeliberationGroup).where(DeliberationGroup.session_id == session_id)).all()
    output = []
    for group in rows:
        members = db.scalars(select(GroupMember).where(GroupMember.group_id == group.id)).all()
        output.append(
            GroupRead(
                id=group.id,
                label=group.label,
                participant_ids=[member.participant_id for member in members],
                risk_score=group.risk_score,
                diversity_score=group.diversity_score,
                bridge_score=group.bridge_score,
                reasoning=group.reasoning,
            )
        )
    return output


@router.get("/mediation-briefs", response_model=list[MediationBriefRead])
def mediation_briefs(session_id: str, db: Session = Depends(get_db)) -> list[MediationBriefRead]:
    rows = db.scalars(select(MediationBrief).where(MediationBrief.session_id == session_id)).all()
    return [
        MediationBriefRead(
            group_id=row.group_id,
            shared_ground=row.shared_ground,
            likely_tensions=row.likely_tensions,
            bridge_questions=row.bridge_questions,
            discussion_order=row.discussion_order,
        )
        for row in rows
    ]


@router.get("/risk-matrix")
def risk_matrix(session_id: str, db: Session = Depends(get_db)) -> list[dict]:
    participants = db.scalars(select(Participant).where(Participant.session_id == session_id)).all()
    claims = db.scalars(select(Claim).where(Claim.session_id == session_id)).all()
    edges = db.scalars(select(ConflictEdge).where(ConflictEdge.session_id == session_id)).all()
    claim_to_participant = {claim.id: claim.participant_id for claim in claims}
    names = {participant.id: participant.display_name for participant in participants}
    rows = []
    for left, right in combinations([p.id for p in participants], 2):
        relevant = [
            edge
            for edge in edges
            if {claim_to_participant.get(edge.source_claim_id), claim_to_participant.get(edge.target_claim_id)}
            == {left, right}
        ]
        risk = max([edge.risk_score for edge in relevant], default=0.12)
        rows.append(
            {
                "pair": [left, right],
                "pair_names": [names[left], names[right]],
                "risk_score": round(risk, 2),
                "reason": relevant[0].reason if relevant else "No direct high-risk claim conflict detected.",
            }
        )
    return sorted(rows, key=lambda item: item["risk_score"], reverse=True)


@router.post("/simulate-live", response_model=LiveIntervention)
async def simulate_live(session_id: str, payload: LiveMessage, db: Session = Depends(get_db)) -> dict:
    if not db.scalars(select(Participant).where(Participant.session_id == session_id)).first():
        raise HTTPException(status_code=404, detail="Session not found")
    return await LiveMediationAgent().run(payload.model_dump())
