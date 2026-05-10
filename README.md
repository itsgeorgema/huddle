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
- Next.js demo cockpit with two intake modes — pre-built scenarios, or describe-your-own conflict that mixes optional CSV-uploaded personas with optional AI-generated personas — plus pipeline status, conflict graph, risk matrix, groups, briefs, and live mediation simulation.

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
4. Pick one of the two intake modes.

### Option A — Check an existing conflict

5. Select a pre-built scenario such as `Affordable Housing vs Parking`.
6. Click `Load and analyze`. The frontend calls `POST /api/demo/scenarios/{id}/load`, then `POST /api/sessions/{id}/analyze`.

### Option B — Describe your own conflict

5. Type a conflict topic.
6. Optionally upload a CSV of your own personas (`display_name`, `statement`, plus any extra columns that are accepted but ignored).
7. Optionally set `AI personas` to 1–15 to have the LLM generate diverse personas spanning age, role, sex, stance, and demographic. When both a CSV and a count are provided, the LLM is told what your real personas already said so it fills viewpoint gaps rather than duplicating them.
8. Click `Compose and analyze`. The frontend calls `POST /api/demo/compose`, then `POST /api/sessions/{id}/analyze`.

### Either path

9. The Fastify gateway proxies the calls to the Python LangGraph agent service.
10. The LangGraph pipeline runs all 7 AI agents sequentially and streams results to the database.
11. Inspect graph, matrix, groups, briefs, and live mediation.

## Bring Your Own Conflict (Option B)

The custom flow accepts a topic plus two optional persona sources — uploaded CSV personas and AI-generated personas — that can be used together or separately. You must supply at least one source.

### CSV format

Required columns: `display_name` and `statement`. Extra columns are accepted but ignored. Rows missing either required value are silently skipped.

```csv
display_name,statement,age,role
Alice Chen,I run a small bookkeeping business out of my home and renting our spare room on weekends pays my health insurance.,34,Homeowner
Marcus Webb,My rent went up 22% last year. Every house turned into an Airbnb is one fewer place a working family can live.,28,Renter
```

### AI persona generation

When `num_ai_personas` is greater than 0, the agent service prompts the LLM to generate that many distinct personas spanning age, role, sex, stance, and demographic background. If a CSV is also provided, the prompt includes the CSV statements as context so the AI fills viewpoint gaps rather than duplicating existing perspectives.

## API Examples

```bash
# Existing-scenario flow
curl -X POST http://localhost:8000/api/demo/scenarios/housing_parking/load
curl -X POST http://localhost:8000/api/sessions/<session_id>/analyze \
  -H 'Content-Type: application/json' \
  -d '{"group_size":4,"constraints":{"max_group_risk":0.75}}'
curl http://localhost:8000/api/sessions/<session_id>/graph

# Custom-conflict flow with mixed CSV + AI personas
curl -X POST http://localhost:8000/api/demo/compose \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "Should our school ban phones during class hours?",
    "csv": "display_name,statement\nAlice,My kid needs phone access for diabetes monitoring.\nBob,Phones distract from learning.",
    "num_ai_personas": 6
  }'
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
