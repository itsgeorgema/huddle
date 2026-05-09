# Agent Pipeline

The MVP pipeline is intentionally multi-agent but deterministic by default.

1. Intake Agent cleans statements, detects basic tone, and preserves language metadata.
2. Claim Extraction Agent splits statements into structured claims with claim type, stakeholder, and value labels.
3. Conflict Classifier Agent compares claims across participants and creates typed conflict edges.
4. Participant Profiler Agent creates lightweight profiles from submitted claims only.
5. Routing Engine assigns participants into balanced groups.
6. Pre-Mediation Agent creates shared ground, tensions, bridge questions, and discussion order.
7. Consensus Summarizer Agent records consensus points, unresolved disagreements, evidence needs, and compromises.
8. Live Mediation Agent simulates circuit-breaker interventions from chat messages.

Real LLM mode is represented by the `LLMProvider` interface, but the MVP defaults to mock mode so demos are stable.
