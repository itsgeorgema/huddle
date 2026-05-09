import asyncio

from app.agents.diversity_load_balancer_agent import DiversityLoadBalancerAgent


def test_diversity_load_balancer_agent_routes_all_participants_into_diverse_groups():
    participants = [{"id": f"p{i}", "display_name": f"P{i}"} for i in range(1, 7)]
    clusters = ["housing", "housing", "business", "business", "accessibility", "transportation"]
    profiles = [
        {
            "participant_id": participant["id"],
            "viewpoint_cluster": cluster,
            "main_values": [cluster],
            "bridge_potential": 0.6,
            "conflict_risk": 0.4,
        }
        for participant, cluster in zip(participants, clusters)
    ]
    claims = [
        {"claim_id": f"c{i}", "participant_id": participant["id"]}
        for i, participant in enumerate(participants, start=1)
    ]
    output = asyncio.run(
        DiversityLoadBalancerAgent().run(
            {
                "participants": participants,
                "profiles": profiles,
                "claims": claims,
                "conflict_edges": [],
                "group_size": 3,
                "constraints": {"max_group_risk": 0.75},
            }
        )
    )
    routed_count = sum(len(group["participant_ids"]) for group in output["groups"])
    assert routed_count == len(participants)
    assert output["routing_policy"]["strategy"] == "langgraph_diversity_balancer"
    assert all(group["diversity_score"] >= 0.5 for group in output["groups"])
