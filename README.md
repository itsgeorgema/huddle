# Huddle

Huddle is a conflict-aware deliberation load balancer. It analyzes participant statements, extracts claims, builds a conflict graph, predicts risky pairings, routes people into balanced discussion groups, and generates AI-powered mediation briefs for productive disagreement.

## What Is Implemented

- TypeScript Fastify API gateway for frontend-facing traffic and shared API contracts.
- Python FastAPI AI agent service with session, participant, analysis, graph, group, risk matrix, demo, live mediation, health, and metrics endpoints.
- LangGraph pipeline for intake, claim extraction, conflict classification, participant profiling, diversity load balancing, pre-mediation briefing, and consensus summary — all backed by real OpenAI LLM calls.
- Real OpenAI embeddings (`text-embedding-3-small`) stored per claim for semantic similarity.
- SQLAlchemy data model for sessions, participants, statements, claims, conflict edges, profiles, groups, briefs, and agent runs.
- NetworkX conflict graph serialization for frontend rendering.
- LangGraph `diversity_load_balancer` agent node with diversity, bridge, risk, and minority-isolation scoring.
- Celery/Redis worker plumbing and Docker Compose stack with Postgres, Redis, Prometheus, and Grafana.
- Next.js demo cockpit with scenario loading, pipeline status, conflict graph, risk matrix, groups, briefs, and live mediation simulation.

## Requirements

- **OpenAI API key** — the pipeline uses `gpt-5.4-mini` by default and `text-embedding-3-small` for embeddings. Set `OPENAI_API_KEY` before starting.

## Quick Start With Docker

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
docker compose up --build
```

Open:

- Web: `http://localhost:3000/demo`
- API gateway health: `http://localhost:8000/health`
- Python agent service docs: `http://localhost:8001/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

## Local Development

Python agent service:

```bash
cd apps/agents
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
OPENAI_API_KEY=sk-... python -m uvicorn app.main:app --reload --port 8001
```

TypeScript API gateway:

```bash
cd apps/api
npm install
AGENTS_URL=http://localhost:8001 npm run dev
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

The Python agent service defaults to local SQLite at `apps/agents/huddle.db` when `DATABASE_URL` is not set.

## Manual Demo Flow

1. Set `OPENAI_API_KEY` in your environment.
2. Start agents, API gateway, and web.
3. Visit `http://localhost:3000/demo`.
4. Load `Affordable Housing vs Parking`.
5. The frontend calls `POST /api/demo/scenarios/{id}/load`, then `POST /api/sessions/{id}/analyze`.
6. The Fastify gateway proxies those calls to the Python LangGraph agent service.
7. The LangGraph pipeline runs all 7 AI agents sequentially and streams results to the database.
8. Inspect graph, matrix, groups, briefs, and live mediation.

## API Examples

```bash
curl -X POST http://localhost:8000/api/demo/scenarios/housing_parking/load
curl -X POST http://localhost:8000/api/sessions/<session_id>/analyze \
  -H 'Content-Type: application/json' \
  -d '{"group_size":4,"constraints":{"max_group_risk":0.75}}'
curl http://localhost:8000/api/sessions/<session_id>/graph
```

## LLM Configuration

The pipeline uses `gpt-5.4-mini` by default. To use a different model:

```bash
LLM_MODEL=gpt-4o OPENAI_API_KEY=...
```

## Architecture Notes

The MVP intentionally uses a polyglot split:

- `apps/web`: Next.js frontend.
- `apps/api`: TypeScript Fastify API gateway for product-facing API, validation boundary, and future SSE/WebSocket endpoints.
- `apps/agents`: Python FastAPI AI/ML service for LangGraph, embeddings, NetworkX, scoring, routing, and mediation.
- `packages/shared-types`: shared TypeScript contracts.

Production evolution:

- Move durable workflow orchestration to Temporal.
- Extract deterministic routing into Go if latency or throughput requires it.
- Add Redpanda/Kafka for event streaming.
- Add a dedicated TypeScript realtime mediation service for WebSockets/SSE.
