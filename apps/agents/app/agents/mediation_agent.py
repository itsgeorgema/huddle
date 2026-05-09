import json
from collections import defaultdict

from app.agents.base import Agent
from app.services.llm_client import LLMClient

_BRIEF_SYSTEM = """\
You are an experienced civic mediator. Generate a pre-mediation brief for a discussion group
about to deliberate on a civic issue.

Return a JSON object with a "briefs" array. Each brief must have:
- group_id          (copy exactly from input)
- shared_ground     list of 2–3 strings — genuine common ground across the group
- likely_tensions   list of 2–4 strings — the most significant disagreements or friction points
- bridge_questions  list of 2–4 open questions that could help the group find common ground
- discussion_order  list of 4–5 steps guiding productive conversation flow

Be specific to the actual claims and values in the group. Avoid generic platitudes.
The goal is productive disagreement, not forced consensus.\
"""

_LIVE_SYSTEM = """\
You are a live civic mediator. Analyze discussion messages and determine if intervention
is needed.

Return a JSON object with:
- event          one of: escalation_detected, evidence_need_detected, stable_discussion
- reason         1–2 sentences explaining what was detected
- intervention   a concrete, specific suggestion for the facilitator

Escalation indicators: personal attacks, motive-questioning, contemptuous language.
Evidence needs: claims about facts that should be verified before continuing.
Stable: productive discussion of tradeoffs and values.\
"""


class PreMediationAgent(Agent):
    name = "pre_mediation"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        groups = payload["groups"]
        claims_by_participant: dict[str, list[dict]] = payload["claims_by_participant"]

        groups_data = []
        for group in groups:
            group_claims = [
                {"text": c["text"], "value": c["value"], "stakeholder": c["stakeholder"]}
                for pid in group["participant_ids"]
                for c in claims_by_participant.get(pid, [])
            ]
            groups_data.append(
                {
                    "group_id": group["id"],
                    "participant_count": len(group["participant_ids"]),
                    "risk_score": group.get("risk_score", 0.5),
                    "diversity_score": group.get("diversity_score", 0.5),
                    "claims": group_claims,
                }
            )

        result = await self.llm.complete_json(_BRIEF_SYSTEM, json.dumps(groups_data, ensure_ascii=False))
        return {"briefs": result.get("briefs", [])}


class LiveMediationAgent(Agent):
    name = "live_mediation"

    def __init__(self) -> None:
        self.llm = LLMClient()

    async def run(self, payload: dict) -> dict:
        messages = payload.get("messages", [])
        user = json.dumps({"messages": messages}, ensure_ascii=False)
        result = await self.llm.complete_json(_LIVE_SYSTEM, user)
        return {
            "event": result.get("event", "stable_discussion"),
            "reason": result.get("reason", ""),
            "intervention": result.get("intervention", "Continue the current discussion order."),
        }
