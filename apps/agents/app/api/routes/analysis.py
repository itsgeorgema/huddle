from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.api.schemas.session import AnalyzeRequest, PipelineStatus, PipelineStep
from app.db.models import AgentRun, SessionModel
from app.db.session import get_db
from app.workers.tasks import analyze_session_task

router = APIRouter(prefix="/sessions/{session_id}", tags=["analysis"])


@router.post("/analyze")
async def analyze(session_id: str, payload: AnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    if not db.get(SessionModel, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    orchestrator = AgentOrchestrator(db)
    return await orchestrator.run(session_id, payload.group_size, payload.constraints)


@router.post("/analyze/queued")
def analyze_queued(session_id: str, payload: AnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    if not db.get(SessionModel, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    task = analyze_session_task.delay(session_id, payload.group_size, payload.constraints)
    return {"task_id": task.id, "status": "queued"}


@router.get("/analysis/status", response_model=PipelineStatus)
def status(session_id: str, db: Session = Depends(get_db)) -> PipelineStatus:
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    runs = db.scalars(
        select(AgentRun).where(AgentRun.session_id == session_id).order_by(AgentRun.created_at.asc())
    ).all()
    return PipelineStatus(
        status=session.status,
        steps=[
            PipelineStep(name=run.agent_name, status=run.status, latency_ms=run.latency_ms, error=run.error)
            for run in runs
        ],
    )
