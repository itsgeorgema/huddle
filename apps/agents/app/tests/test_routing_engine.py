from app.services.routing_engine import RoutingEngine


def test_router_balances_clusters_across_groups():
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
    groups = RoutingEngine().route(participants, profiles, {}, group_size=3)
    assert len(groups) == 2
    assert all(group["diversity_score"] > 0.5 for group in groups)
