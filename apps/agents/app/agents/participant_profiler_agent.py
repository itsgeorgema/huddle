import json
from collections import defaultdict

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_SYSTEM = """\
You are a civic deliberation profiler. Based on each participant's claims and their
conflict involvement, create a deliberation profile.

Return a JSON object with a "profiles" array. Each profile must have:
- participant_id      (copy exactly from input)
- viewpoint_cluster   a short snake_case label for the participant's dominant viewpoint,
                      e.g. "housing_access", "business_parking", "transit_climate",
                      "accessibility_concern", "public_trust"
- main_values         list of 1–4 value strings from the participant's claims
- conflict_risk       float 0.0–1.0 — how much conflict this participant is involved in
- bridge_potential    float 0.0–1.0 — how well this participant could bridge opposing views

Important: do NOT infer ethnicity, gender, political party, or any protected characteristic.
Base profiles only on the content of submitted statements.\
"""


class ParticipantProfilerAgent(Agent):
    name = "participant_profiling"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        claims = payload["claims"]
        edges = payload["conflict_edges"]

        by_participant: dict[str, list[dict]] = defaultdict(list)
        for claim in claims:
            by_participant[claim["participant_id"]].append(claim)

        conflict_counts: dict[str, int] = defaultdict(int)
        claim_to_participant = {c["claim_id"]: c["participant_id"] for c in claims}
        for edge in edges:
            src_pid = claim_to_participant.get(edge.get("source_claim", ""))
            tgt_pid = claim_to_participant.get(edge.get("target_claim", ""))
            if src_pid:
                conflict_counts[src_pid] += 1
            if tgt_pid:
                conflict_counts[tgt_pid] += 1

        participants_data = [
            {
                "participant_id": pid,
                "claims": [
                    {"text": c["text"], "value": c["value"], "stakeholder": c["stakeholder"]}
                    for c in pclaims
                ],
                "conflict_edge_count": conflict_counts[pid],
            }
            for pid, pclaims in by_participant.items()
        ]

        result = await self.llm.complete_json(_SYSTEM, json.dumps(participants_data, ensure_ascii=False))
        return {"profiles": result.get("profiles", [])}
