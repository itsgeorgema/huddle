import os

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.db.base import init_db
from app.db.models import Participant, SessionModel, Statement
from app.db.session import SessionLocal


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_orchestrator_runs_langgraph_pipeline():
    init_db()
    db = SessionLocal()
    try:
        session = SessionModel(title="Test", description="Test")
        db.add(session)
        db.flush()
        for name, text in [
            ("Maya", "We need affordable housing."),
            ("Jordan", "Parking matters for business customers."),
            ("Luis", "Transit can reduce car dependency."),
            ("Evelyn", "Accessible parking still matters."),
        ]:
            participant = Participant(session_id=session.id, display_name=name)
            db.add(participant)
            db.flush()
            db.add(Statement(session_id=session.id, participant_id=participant.id, text=text))
        db.commit()
        result = await AgentOrchestrator(db).run(session.id, group_size=4)
        assert result["status"] == "complete"
        assert result["routing_policy"]["strategy"] == "langgraph_diversity_balancer"
        assert result["groups"] >= 1
        assert result["claims"] >= 4
    finally:
        db.close()
