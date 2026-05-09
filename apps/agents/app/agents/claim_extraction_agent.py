import json

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_SYSTEM = """\
You are a civic deliberation analyst. Extract structured claims from participant statements.

Return a JSON object with a "claims" array. Each claim must have:
- claim_id   string like "c{statement_index}_{claim_index}" (1-based, e.g. "c1_1", "c1_2", "c2_1")
- participant_id   (copy exactly from the statement)
- statement_id     (copy exactly from the statement)
- text    the specific claim in 1-2 sentences
- claim_type   one of: proposal, impact, priority, concern, factual
- stakeholder  the group most directly affected, e.g. "renters", "business owners",
               "elderly residents", "students", "transit riders", "residents", "general public"
- value   the core value at stake, e.g. "housing access", "business access",
          "transportation", "accessibility", "public trust", "climate", "safety",
          "student wellbeing", "economic stability", "community benefit"
- confidence  float 0.0–1.0

Extract 1–3 distinct, meaningful claims per statement. Avoid trivial or redundant splits.\
"""


class ClaimExtractionAgent(Agent):
    name = "claim_extraction"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        statements = payload["statements"]
        rows = [
            {
                "statement_index": i,
                "statement_id": s["statement_id"],
                "participant_id": s["participant_id"],
                "text": s["cleaned_statement"],
            }
            for i, s in enumerate(statements, start=1)
        ]
        result = await self.llm.complete_json(_SYSTEM, json.dumps(rows, ensure_ascii=False))
        return {"claims": result.get("claims", [])}
