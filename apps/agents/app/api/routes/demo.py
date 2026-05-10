import csv
import io
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas.session import SessionRead
from app.db.models import Participant, SessionModel, Statement
from app.db.session import get_db
from app.services.llm_client import LLMClient

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
        participants = data.get("participants", [])
        output.append({
            "id": path.stem,
            "title": data["title"],
            "description": data["description"],
            "participant_count": len(participants),
            "participants": [
                {"name": p["name"], "statement": p["statement"]}
                for p in participants
            ],
        })
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


class ComposeRequest(BaseModel):
    topic: str = Field(min_length=10, max_length=2000)
    csv: str | None = None
    num_ai_personas: int = Field(default=0, ge=0, le=15)


GENERATE_SYSTEM_PROMPT = (
    "You generate diverse personas for civic deliberation. Given a conflict topic, you produce "
    "a set of distinct personas. Each persona must have a realistic first name and a substantive "
    "statement (2-4 sentences) reflecting their lived perspective on the conflict.\n\n"
    "The personas MUST be diverse across these dimensions:\n"
    "- Age: include young, middle-aged, and elderly voices.\n"
    "- Role / stakeholder: vary roles such as parent, student, teacher, business owner, "
    "professional, retiree, organizer, public worker, etc., as appropriate to the topic.\n"
    "- Sex / gender: include a mix of representation.\n"
    "- Stance: span pro, against, ambivalent, and unconventional positions on the conflict — "
    "not all on one side.\n"
    "- Demographic background: vary ethnicity, socioeconomic level, geographic context, and "
    "cultural background where relevant.\n\n"
    "Each statement should sound like the persona's own voice and reflect their specific stake "
    "in the issue. Avoid generic talking points. Names should be realistic and span cultures.\n\n"
    'Return strict JSON of the form: {"personas": [{"name": "...", "statement": "..."}, ...]}'
)


def _parse_csv_rows(csv_text: str) -> list[tuple[str, str]]:
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    parsed: list[tuple[str, str]] = []
    for row in rows:
        name = (row.get("display_name") or row.get("name") or "").strip()
        statement = (row.get("statement") or "").strip()
        if name and statement:
            parsed.append((name[:160], statement))
    return parsed


async def _generate_ai_personas(topic: str, count: int, existing_statements: list[str]) -> list[tuple[str, str]]:
    if count <= 0:
        return []
    llm = LLMClient()
    user_prompt_lines = [f"Conflict topic:\n{topic}"]
    if existing_statements:
        joined = "\n".join(f"- {statement}" for statement in existing_statements)
        user_prompt_lines.append(
            "\nThe following real participants are already in the room. Generate AI personas "
            "that fill viewpoint gaps and bring perspectives not yet represented:\n" + joined
        )
    user_prompt_lines.append(f"\nGenerate exactly {count} diverse personas as specified.")
    user_prompt = "\n".join(user_prompt_lines)
    response = await llm.complete_json(GENERATE_SYSTEM_PROMPT, user_prompt, temperature=0.85)
    personas = response.get("personas") or []
    if not isinstance(personas, list):
        return []
    out: list[tuple[str, str]] = []
    for item in personas:
        name = (item.get("name") or "").strip()
        statement = (item.get("statement") or "").strip()
        if name and statement:
            out.append((name[:160], statement))
    return out


@router.post("/compose", response_model=SessionRead)
async def compose(payload: ComposeRequest, db: Session = Depends(get_db)) -> SessionModel:
    csv_personas = _parse_csv_rows(payload.csv) if payload.csv else []
    if not csv_personas and payload.num_ai_personas == 0:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one persona source: a CSV file or AI personas (1-15).",
        )

    ai_personas = await _generate_ai_personas(
        payload.topic,
        payload.num_ai_personas,
        [statement for _, statement in csv_personas],
    )

    if not csv_personas and not ai_personas:
        raise HTTPException(status_code=502, detail="No usable personas were produced")

    title = payload.topic.strip()[:240]
    parts = []
    if csv_personas:
        parts.append(f"{len(csv_personas)} uploaded")
    if ai_personas:
        parts.append(f"{len(ai_personas)} AI-generated")
    description = f"Custom room ({', '.join(parts)}): {title}"

    session = SessionModel(title=title, description=description[:1000], status="draft")
    db.add(session)
    db.flush()

    for name, statement in (*csv_personas, *ai_personas):
        participant = Participant(session_id=session.id, display_name=name)
        db.add(participant)
        db.flush()
        db.add(Statement(session_id=session.id, participant_id=participant.id, text=statement))

    db.commit()
    db.refresh(session)
    return session
