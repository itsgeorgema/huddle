from app.agents.base import Agent


class IntakeAgent(Agent):
    name = "intake"

    async def run(self, payload: dict) -> dict:
        results = []
        for statement in payload["statements"]:
            text = " ".join(statement["text"].split())
            lower = text.lower()
            tone = "assertive"
            if any(word in lower for word in ["never", "ignored", "don't care", "angry"]):
                tone = "frustrated"
            elif any(word in lower for word in ["maybe", "concern", "support, but", "worry"]):
                tone = "concerned"
            results.append(
                {
                    "statement_id": statement["id"],
                    "participant_id": statement["participant_id"],
                    "cleaned_statement": text,
                    "detected_tone": tone,
                    "language": "en",
                }
            )
        return {"statements": results}
