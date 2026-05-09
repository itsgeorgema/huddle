# Huddle Architecture

Huddle is a distributed deliberation orchestration platform. It treats difficult group discussion like a load-balancing problem: inspect incoming statements, model claims and conflicts, predict overload, and route participants into groups with explainable mediation briefs.

## Components

- Next.js frontend for the demo cockpit.
- TypeScript Fastify API gateway for public REST traffic, frontend-facing contracts, and future realtime/SSE entrypoints.
- Python FastAPI AI agent service for LangGraph, embeddings, NetworkX, routing, graph, and mediation endpoints.
- Celery worker with Redis broker for queued analysis jobs during the MVP.
- SQLAlchemy persistence over SQLite locally or Postgres/pgvector in Docker.
- LangGraph agent pipeline for intake, claim extraction, conflict classification, profiles, diversity load balancing, mediation, and summaries.
- NetworkX graph service for participant, claim, value, and conflict topology.
- Routing engine currently runs in Python inside the LangGraph `diversity_load_balancer` node.
- Prometheus metrics endpoint and Compose-managed Prometheus/Grafana.

## Service Split

```text
apps/web      Next.js + TypeScript
apps/api      TypeScript Fastify API gateway
apps/agents   Python FastAPI + LangGraph AI/ML service
apps/routing  Future Go routing service extraction point
```

Python is intentionally limited to the AI/ML and graph-algorithm layer where the ecosystem is strongest. Product-facing API and future realtime mediation belong in TypeScript. The routing core is designed so it can later move to Go without changing the frontend contract.

## Runtime Flow

1. Organizer loads a scenario or creates a session.
2. Participant statements are persisted.
3. Gateway forwards analysis to the Python agent service.
4. Analysis runs through the LangGraph pipeline.
5. Claims, conflict edges, profiles, groups, and briefs are persisted.
6. Frontend fetches graph, risk matrix, groups, briefs, and live interventions through the gateway.
