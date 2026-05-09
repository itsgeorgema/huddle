# Huddle Architecture

Huddle is a distributed deliberation orchestration platform. It treats difficult group discussion like a load-balancing problem: inspect incoming statements, model claims and conflicts, predict overload, and route participants into groups with explainable mediation briefs.

## Components

- FastAPI API gateway for sessions, participants, analysis, graph, groups, and live simulation.
- Celery worker with Redis broker for queued analysis jobs.
- SQLAlchemy persistence over SQLite locally or Postgres/pgvector in Docker.
- Agent pipeline for intake, claim extraction, conflict classification, profiles, mediation, and summaries.
- NetworkX graph service for participant, claim, value, and conflict topology.
- Routing engine for diversity, bridge, conflict-risk, and minority-isolation scoring.
- Next.js demo cockpit for reliable end-to-end demos.
- Prometheus metrics endpoint and Compose-managed Prometheus/Grafana.

## Runtime Flow

1. Organizer loads a scenario or creates a session.
2. Participant statements are persisted.
3. Analysis runs through deterministic mock agents.
4. Claims, conflict edges, profiles, groups, and briefs are persisted.
5. Frontend fetches graph, risk matrix, groups, briefs, and live interventions.
