import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.session import SessionRead
from app.db.models import Participant, SessionModel, Statement
from app.db.session import get_db

router = APIRouter(prefix="/demo", tags=["demo"])


def _demo_data_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "packages" / "demo-data"
        if candidate.exists():
            return candidate
    return Path("/app/packages/demo-data")


DATA_DIR = _demo_data_dir()


@router.get("/scenarios")
def scenarios() -> list[dict]:
    output = []
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        output.append({"id": path.stem, "title": data["title"], "description": data["description"]})
    return output


@router.post("/scenarios/{scenario_id}/load", response_model=SessionRead)
def load_scenario(scenario_id: str, db: Session = Depends(get_db)) -> SessionModel:
    path = DATA_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    data = json.loads(path.read_text())
    session = SessionModel(title=data["title"], description=data["description"], status="draft")
    db.add(session)
    db.flush()
    for item in data["participants"]:
        participant = Participant(session_id=session.id, display_name=item["name"])
        db.add(participant)
        db.flush()
        db.add(Statement(session_id=session.id, participant_id=participant.id, text=item["statement"]))
    db.commit()
    db.refresh(session)
    return session
