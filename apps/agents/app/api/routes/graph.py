from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.claim import ClaimRead, ConflictEdgeRead
from app.api.schemas.graph import GraphResponse
from app.db.models import Claim, ConflictEdge, Participant, ParticipantProfile
from app.db.session import get_db
from app.services.graph_service import ConflictGraphService

router = APIRouter(prefix="/sessions/{session_id}", tags=["graph"])


@router.get("/claims", response_model=list[ClaimRead])
def claims(session_id: str, db: Session = Depends(get_db)) -> list[Claim]:
    return list(db.scalars(select(Claim).where(Claim.session_id == session_id)).all())


@router.get("/conflicts", response_model=list[ConflictEdgeRead])
def conflicts(session_id: str, db: Session = Depends(get_db)) -> list[ConflictEdge]:
    return list(db.scalars(select(ConflictEdge).where(ConflictEdge.session_id == session_id)).all())


@router.get("/graph", response_model=GraphResponse)
def graph(session_id: str, db: Session = Depends(get_db)) -> dict:
    participants = [
        {"id": p.id, "display_name": p.display_name}
        for p in db.scalars(select(Participant).where(Participant.session_id == session_id)).all()
    ]
    if not participants:
        raise HTTPException(status_code=404, detail="No participants found for session")
    claims = [
        {
            "claim_id": c.id,
            "participant_id": c.participant_id,
            "text": c.text,
            "claim_type": c.claim_type,
            "stakeholder": c.stakeholder,
            "value": c.value_label,
        }
        for c in db.scalars(select(Claim).where(Claim.session_id == session_id)).all()
    ]
    conflicts = [
        {
            "source_claim": e.source_claim_id,
            "target_claim": e.target_claim_id,
            "edge_type": e.edge_type,
            "conflict_type": e.conflict_type,
            "risk_score": e.risk_score,
            "reason": e.reason,
        }
        for e in db.scalars(select(ConflictEdge).where(ConflictEdge.session_id == session_id)).all()
    ]
    profiles = [
        {
            "participant_id": p.participant_id,
            "viewpoint_cluster": p.viewpoint_cluster,
            "main_values": p.main_values,
            "bridge_potential": p.bridge_score,
            "conflict_risk": p.conflict_risk,
        }
        for p in db.scalars(select(ParticipantProfile).where(ParticipantProfile.session_id == session_id)).all()
    ]
    service = ConflictGraphService()
    return service.serialize(service.build(participants, claims, conflicts, profiles))
