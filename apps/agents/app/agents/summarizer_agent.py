import json

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_SYSTEM = """\
You are a civic deliberation analyst. Summarize the outcomes from a civic discussion
based on extracted claims and detected conflicts.

Return a JSON object with:
- consensus_points        list of 2–4 strings — views or priorities that most participants share
- unresolved_disagreements list of 2–4 strings — genuine disagreements that remain open
- evidence_needed         list of 1–3 strings — factual questions that need data to resolve
- possible_compromises    list of 2–3 strings — realistic compromise options that could satisfy
                          multiple stakeholder groups

Be specific to the actual content. Do not invent positions not present in the claims.\
"""


class ConsensusSummarizerAgent(Agent):
    name = "consensus_summary"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        claims = [{"text": c["text"], "value": c["value"], "stakeholder": c["stakeholder"]} for c in payload["claims"]]
        edges = [{"reason": e["reason"], "conflict_type": e["conflict_type"], "risk_score": e["risk_score"]} for e in payload["conflict_edges"]]
        user = json.dumps({"claims": claims, "conflict_edges": edges}, ensure_ascii=False)
        result = await self.llm.complete_json(_SYSTEM, user)
        return {
            "consensus_points": result.get("consensus_points", []),
            "unresolved_disagreements": result.get("unresolved_disagreements", []),
            "evidence_needed": result.get("evidence_needed", []),
            "possible_compromises": result.get("possible_compromises", []),
        }
