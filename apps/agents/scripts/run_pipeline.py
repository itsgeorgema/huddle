import asyncio
import sys

from app.agents.orchestrator import AgentOrchestrator
from app.db.base import init_db
from app.db.session import SessionLocal


async def main(session_id: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        result = await AgentOrchestrator(db).run(session_id=session_id, group_size=4)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/run_pipeline.py <session_id>")
    asyncio.run(main(sys.argv[1]))
