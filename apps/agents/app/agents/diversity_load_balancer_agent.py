from app.agents.base import Agent
from app.services.routing_engine import RoutingEngine
from app.services.scoring_service import ScoringService


class DiversityLoadBalancerAgent(Agent):
    """LangGraph node agent that evaluates routing policy and assigns groups."""

    name = "diversity_load_balancer"

    def __init__(self) -> None:
        self.scoring = ScoringService()
        self.router = RoutingEngine()

    async def run(self, payload: dict) -> dict:
        participants = payload["participants"]
        profiles = payload["profiles"]
        claims = payload["claims"]
        conflict_edges = payload["conflict_edges"]
        group_size = payload.get("group_size", 4)
        constraints = payload.get("constraints") or {}
        claim_to_participant = {claim["claim_id"]: claim["participant_id"] for claim in claims}
        pairwise = self.scoring.pairwise_risk(
            [participant["id"] for participant in participants],
            claim_to_participant,
            conflict_edges,
        )
        groups = self.router.route(participants, profiles, pairwise, group_size, constraints)
        return {
            "pairwise_risk": pairwise,
            "groups": groups,
            "routing_policy": {
                "strategy": "langgraph_diversity_balancer",
                "objectives": [
                    "maximize viewpoint diversity",
                    "keep conflict risk manageable",
                    "place bridge participants into mixed groups",
                    "avoid isolated minority viewpoints",
                ],
                "constraints": constraints,
                "group_size": group_size,
            },
        }
