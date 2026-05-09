import json

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_SYSTEM = """\
You are a civic deliberation assistant. For each participant statement, clean the text
and assess the speaker's tone.

Return a JSON object with a "statements" array. Each element must have:
- statement_id  (copy exactly from input)
- participant_id  (copy exactly from input)
- cleaned_statement  (corrected spelling, normalized whitespace, no content changes)
- detected_tone  (one of: assertive, frustrated, concerned, neutral, collaborative)
- language  (ISO 639-1 code; default "en")

Preserve every participant's original meaning. Do not paraphrase or editorialize.\
"""


class IntakeAgent(Agent):
    name = "intake"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        statements = payload["statements"]
        user = json.dumps(
            [{"statement_id": s["id"], "participant_id": s["participant_id"], "text": s["text"]} for s in statements],
            ensure_ascii=False,
        )
        result = await self.llm.complete_json(_SYSTEM, user)
        return {"statements": result.get("statements", [])}
