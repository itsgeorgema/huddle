import asyncio

from app.agents.orchestrator import AgentOrchestrator
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(name="huddle.analyze_session")
def analyze_session_task(session_id: str, group_size: int = 4, constraints: dict | None = None) -> dict:
    db = SessionLocal()
    try:
        return asyncio.run(AgentOrchestrator(db).run(session_id, group_size, constraints or {}))
    finally:
        db.close()
