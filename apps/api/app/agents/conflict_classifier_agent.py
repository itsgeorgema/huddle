from itertools import combinations

from app.agents.base import Agent


OPPOSITION = [
    ("housing access", "business access", "value_conflict"),
    ("housing access", "transportation", "impact_conflict"),
    ("business access", "transportation", "impact_conflict"),
    ("business access", "climate", "value_conflict"),
    ("student wellbeing", "public trust", "stakeholder_conflict"),
    ("safety", "public trust", "value_conflict"),
]


class ConflictClassifierAgent(Agent):
    name = "conflict_classification"

    async def run(self, payload: dict) -> dict:
        claims = payload["claims"]
        edges = []
        for left, right in combinations(claims, 2):
            if left["participant_id"] == right["participant_id"]:
                continue
            edge = self._classify_pair(left, right)
            if edge:
                edges.append(edge)
        return {"conflict_edges": edges}

    def _classify_pair(self, left: dict, right: dict) -> dict | None:
        left_value = left["value"]
        right_value = right["value"]
        pair_values = {left_value, right_value}
        conflict_type = None
        for a, b, kind in OPPOSITION:
            if {a, b} == pair_values:
                conflict_type = kind
                break
        tone_boost = 0.08 if "never" in left["text"].lower() or "never" in right["text"].lower() else 0
        stakeholder_boost = 0.08 if left["stakeholder"] != right["stakeholder"] else 0
        direct_boost = 0.1 if self._direct_terms(left["text"], right["text"]) else 0
        if not conflict_type and stakeholder_boost + direct_boost < 0.12:
            return None
        risk = min(0.92, 0.42 + stakeholder_boost + direct_boost + tone_boost + (0.22 if conflict_type else 0))
        if risk < 0.5:
            return None
        return {
            "source_claim": left["claim_id"],
            "target_claim": right["claim_id"],
            "edge_type": "conflicts_with",
            "conflict_type": conflict_type or "stakeholder_conflict",
            "risk_score": round(risk, 2),
            "reason": (
                f"{left['value']} from {left['stakeholder']} may conflict with "
                f"{right['value']} from {right['stakeholder']}."
            ),
        }

    def _direct_terms(self, left: str, right: str) -> bool:
        combined = f"{left.lower()} {right.lower()}"
        return any(term in combined for term in ["hurt", "oppose", "remove", "ban", "increase"])
