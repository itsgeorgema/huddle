# Agent Pipeline

Huddle uses a 7-step LangGraph pipeline. Each step is an AI agent backed by real OpenAI LLM calls (`gpt-5.4-mini` by default). Claims are embedded with `text-embedding-3-small` for semantic storage.

## Pipeline Steps

1. **Intake Agent** — Cleans statements, detects tone (`assertive`, `frustrated`, `concerned`, `neutral`, `collaborative`), and identifies language.
2. **Claim Extraction Agent** — Extracts 1–3 structured claims per statement with `claim_type`, `stakeholder`, `value`, and `confidence`.
3. **Conflict Classifier Agent** — Identifies all significant conflicts between claims from different participants. Returns typed edges with `risk_score` and reasoning.
4. **Participant Profiler Agent** — Builds a deliberation profile per participant: `viewpoint_cluster`, `main_values`, `conflict_risk`, `bridge_potential`.
5. **Diversity Load Balancer Agent** — Deterministic greedy algorithm that routes participants into groups maximizing diversity and bridge coverage while minimizing conflict overload and minority isolation.
6. **Pre-Mediation Agent** — Generates a group-specific brief: shared ground, likely tensions, bridge questions, and structured discussion order.
7. **Consensus Summarizer Agent** — Synthesizes consensus points, unresolved disagreements, evidence needs, and possible compromises.

## LangGraph Shape

```text
intake
→ claim_extraction
→ conflict_classification
→ participant_profiling
→ diversity_load_balancing
→ pre_mediation
→ consensus_summary
```

## Embeddings

Each extracted claim is embedded with `text-embedding-3-small` (512 dimensions) via batch API call and stored in the `claims` table for future semantic similarity search.

## Observability

Every agent execution is logged to `agent_runs` with status, latency, input/output JSON, and errors. Prometheus metrics track `agent_latency_ms`, `agent_failures_total`, and `pipeline_runs_total`.
