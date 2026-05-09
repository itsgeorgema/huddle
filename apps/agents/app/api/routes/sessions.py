from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.participant import ParticipantBatchCreate, ParticipantRead
from app.api.schemas.session import SessionCreate, SessionRead
from app.db.models import Participant, SessionModel, Statement
from app.db.session import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionModel:
    session = SessionModel(title=payload.title, description=payload.description)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionRead])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionModel]:
    return list(db.scalars(select(SessionModel).order_by(SessionModel.created_at.desc())).all())


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionModel:
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/participants", response_model=list[ParticipantRead])
def add_participants(session_id: str, payload: ParticipantBatchCreate, db: Session = Depends(get_db)) -> list[ParticipantRead]:
    if not db.get(SessionModel, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    response = []
    for item in payload.participants:
        participant = Participant(session_id=session_id, display_name=item.display_name)
        db.add(participant)
        db.flush()
        statement = Statement(session_id=session_id, participant_id=participant.id, text=item.statement)
        db.add(statement)
        response.append(ParticipantRead(id=participant.id, display_name=participant.display_name, statement=item.statement))
    db.commit()
    return response


@router.get("/{session_id}/participants", response_model=list[ParticipantRead])
def list_participants(session_id: str, db: Session = Depends(get_db)) -> list[ParticipantRead]:
    rows = db.execute(
        select(Participant, Statement)
        .join(Statement, Statement.participant_id == Participant.id)
        .where(Participant.session_id == session_id)
    ).all()
    return [ParticipantRead(id=p.id, display_name=p.display_name, statement=s.text) for p, s in rows]
