# Huddle

Huddle is a conflict-aware deliberation load balancer. It analyzes participant statements, extracts claims, builds a conflict graph, predicts risky pairings, routes people into balanced discussion groups, and generates mediation briefs for productive disagreement.

## What Is Implemented

- FastAPI backend with session, participant, analysis, graph, group, risk matrix, demo, live mediation, health, and metrics endpoints.
- Multi-agent mock pipeline for intake, claims, conflict classification, profiles, routing, mediation, and summary.
- SQLAlchemy data model for sessions, participants, statements, claims, conflict edges, profiles, groups, briefs, and agent runs.
- NetworkX conflict graph serialization for frontend rendering.
- Greedy routing engine with diversity, bridge, risk, and minority-isolation scoring.
- Celery/Redis worker plumbing and Docker Compose stack with Postgres, Redis, Prometheus, and Grafana.
- Next.js demo cockpit with scenario loading, pipeline status, conflict graph, risk matrix, groups, briefs, and live mediation simulation.

## Quick Start With Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Web: `http://localhost:3000/demo`
- API docs: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

## Local Development

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

The API defaults to local SQLite at `apps/api/huddle.db` when `DATABASE_URL` is not set.

## Manual Demo Flow

1. Start API and web.
2. Visit `http://localhost:3000/demo`.
3. Load `Affordable Housing vs Parking`.
4. The frontend calls `POST /api/demo/scenarios/{id}/load`, then `POST /api/sessions/{id}/analyze`.
5. Inspect graph, matrix, groups, briefs, and live mediation.

## API Examples

```bash
curl -X POST http://localhost:8000/api/demo/scenarios/housing_parking/load
curl -X POST http://localhost:8000/api/sessions/<session_id>/analyze \
  -H 'Content-Type: application/json' \
  -d '{"mode":"mock","group_size":4,"constraints":{"max_group_risk":0.75}}'
curl http://localhost:8000/api/sessions/<session_id>/graph
```

## Real LLM Mode

Mock mode is the reliable default. To use OpenAI-backed calls later, set:

```bash
LLM_MODE=real
OPENAI_API_KEY=...
```

The provider interface is present, but the current deterministic agents do not require an LLM for the core demo.
