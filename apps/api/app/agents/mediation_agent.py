from collections import Counter

from app.agents.base import Agent


class PreMediationAgent(Agent):
    name = "pre_mediation"

    async def run(self, payload: dict) -> dict:
        briefs = []
        claims_by_participant = payload["claims_by_participant"]
        for group in payload["groups"]:
            group_claims = [
                claim
                for participant_id in group["participant_ids"]
                for claim in claims_by_participant.get(participant_id, [])
            ]
            values = Counter(claim["value"] for claim in group_claims)
            stakeholders = Counter(claim["stakeholder"] for claim in group_claims)
            top_values = [value for value, _ in values.most_common(3)]
            top_stakeholders = [stakeholder for stakeholder, _ in stakeholders.most_common(3)]
            briefs.append(
                {
                    "group_id": group["id"],
                    "shared_ground": self._shared_ground(top_values),
                    "likely_tensions": self._tensions(top_values, top_stakeholders),
                    "bridge_questions": self._questions(top_values),
                    "discussion_order": [
                        "Clarify factual assumptions",
                        "Name the values behind each concern",
                        "Discuss tradeoffs and affected stakeholders",
                        "Generate compromise options",
                        "Record unresolved evidence needs",
                    ],
                }
            )
        return {"briefs": briefs}

    def _shared_ground(self, values: list[str]) -> list[str]:
        ground = ["Participants want the decision to serve the community responsibly."]
        if "housing access" in values and "business access" in values:
            ground.append("Participants care about a livable neighborhood with reliable access.")
        if "transportation" in values:
            ground.append("Participants recognize transportation design affects daily life.")
        return ground

    def _tensions(self, values: list[str], stakeholders: list[str]) -> list[str]:
        tensions = []
        if "housing access" in values and "business access" in values:
            tensions.append("Housing access vs. parking and customer access")
        if "transportation" in values and "business access" in values:
            tensions.append("Mode shift goals vs. short-term business impacts")
        if len(stakeholders) > 1:
            tensions.append(f"Different impacts across {', '.join(stakeholders[:3])}")
        return tensions or ["Different priorities may surface as participants compare tradeoffs."]

    def _questions(self, values: list[str]) -> list[str]:
        questions = ["What evidence would help separate factual uncertainty from value disagreement?"]
        if "housing access" in values and "business access" in values:
            questions.insert(0, "What design changes could add housing while protecting customer access?")
        if "accessibility" in values:
            questions.append("Which accessibility protections should be treated as non-negotiable?")
        return questions


class LiveMediationAgent(Agent):
    name = "live_mediation"

    async def run(self, payload: dict) -> dict:
        text = " ".join(payload.get("messages", [])).lower()
        if any(term in text for term in ["you people", "they never", "don't care", "liar", "stupid"]):
            return {
                "event": "escalation_detected",
                "reason": "Participants are shifting from policy tradeoffs to assumptions about motives.",
                "intervention": "Ask each participant to restate the other side's concern before responding.",
            }
        if any(term in text for term in ["prove", "study", "data", "evidence"]):
            return {
                "event": "evidence_need_detected",
                "reason": "The exchange depends on a factual claim that should be separated from values.",
                "intervention": "Park the factual dispute as an evidence need and continue with values and tradeoffs.",
            }
        return {
            "event": "stable_discussion",
            "reason": "No escalation pattern was detected in the provided messages.",
            "intervention": "Continue the current discussion order.",
        }
