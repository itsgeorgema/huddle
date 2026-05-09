from app.agents.base import Agent


class ConsensusSummarizerAgent(Agent):
    name = "consensus_summary"

    async def run(self, payload: dict) -> dict:
        values = sorted({claim["value"] for claim in payload["claims"]})
        return {
            "consensus_points": [
                "Participants share interest in a decision process that acknowledges tradeoffs.",
                f"Recurring values include {', '.join(values[:4])}.",
            ],
            "unresolved_disagreements": [
                edge["reason"] for edge in payload["conflict_edges"][:5]
            ],
            "evidence_needed": [
                "Impact data for the most disputed claims",
                "Stakeholder-specific cost and access analysis",
            ],
            "possible_compromises": [
                "Pair the preferred policy with targeted mitigations for the most affected stakeholders.",
                "Pilot the change with explicit review criteria before permanent adoption.",
            ],
        }
