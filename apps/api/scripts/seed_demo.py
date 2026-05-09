import json
from pathlib import Path

from app.db.base import init_db
from app.db.models import Participant, SessionModel, Statement
from app.db.session import SessionLocal

def root_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "packages" / "demo-data").exists():
            return parent
    return Path("/app")


ROOT = root_dir()
SCENARIO = ROOT / "packages" / "demo-data" / "housing_parking.json"


def main() -> None:
    init_db()
    data = json.loads(SCENARIO.read_text())
    db = SessionLocal()
    try:
        session = SessionModel(title=data["title"], description=data["description"])
        db.add(session)
        db.flush()
        for item in data["participants"]:
            participant = Participant(session_id=session.id, display_name=item["name"])
            db.add(participant)
            db.flush()
            db.add(Statement(session_id=session.id, participant_id=participant.id, text=item["statement"]))
        db.commit()
        print(session.id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
