import json

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_SYSTEM = """\
You are a civic deliberation conflict analyst. Given a list of claims from different
participants, identify all significant conflicts between claims from different participants.

Return a JSON object with a "conflict_edges" array. Each edge must have:
- source_claim   the claim_id of the first claim (copy EXACTLY from input)
- target_claim   the claim_id of the second claim (copy EXACTLY from input)
- edge_type      always "conflicts_with"
- conflict_type  one of: value_conflict, impact_conflict, stakeholder_conflict,
                 factual_conflict, tone_conflict
- risk_score     float 0.0–1.0 — how likely this conflict derails productive discussion
- reason         1–2 sentences explaining the conflict

Rules:
- Only produce edges between claims from DIFFERENT participants.
- Only include edges with risk_score >= 0.45.
- Use the EXACT claim_id strings from the input — do not invent new ones.
- Focus on substantive disagreements, not superficial wording differences.\
"""


class ConflictClassifierAgent(Agent):
    name = "conflict_classification"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        claims = payload["claims"]
        slim = [
            {
                "claim_id": c["claim_id"],
                "participant_id": c["participant_id"],
                "text": c["text"],
                "value": c["value"],
                "stakeholder": c["stakeholder"],
            }
            for c in claims
        ]
        result = await self.llm.complete_json(_SYSTEM, json.dumps(slim, ensure_ascii=False))
        raw_edges = result.get("conflict_edges", [])

        valid_ids = {c["claim_id"] for c in claims}
        edges = [
            e
            for e in raw_edges
            if (
                e.get("source_claim") in valid_ids
                and e.get("target_claim") in valid_ids
                and e.get("source_claim") != e.get("target_claim")
            )
        ]
        return {"conflict_edges": edges}
