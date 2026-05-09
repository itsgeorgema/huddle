from prometheus_client import Counter, Histogram, generate_latest

AGENT_LATENCY = Histogram("agent_latency_ms", "Agent latency in milliseconds", ["agent"])
AGENT_FAILURES = Counter("agent_failures_total", "Agent failures", ["agent"])
PIPELINE_RUNS = Counter("pipeline_runs_total", "Pipeline runs", ["mode", "status"])


def metrics_response() -> bytes:
    return generate_latest()
