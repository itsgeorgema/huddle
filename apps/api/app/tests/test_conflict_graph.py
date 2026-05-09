from app.services.graph_service import ConflictGraphService


def test_graph_serializes_participant_claim_and_conflict_edges():
    service = ConflictGraphService()
    graph = service.build(
        participants=[{"id": "p1", "display_name": "Maya"}, {"id": "p2", "display_name": "Jordan"}],
        claims=[
            {"claim_id": "c1", "participant_id": "p1", "text": "Build housing", "claim_type": "proposal", "stakeholder": "renters", "value": "housing access"},
            {"claim_id": "c2", "participant_id": "p2", "text": "Keep parking", "claim_type": "concern", "stakeholder": "business owners", "value": "business access"},
        ],
        conflict_edges=[{"source_claim": "c1", "target_claim": "c2", "edge_type": "conflicts_with", "conflict_type": "value_conflict", "risk_score": 0.82, "reason": "Housing vs parking"}],
        profiles=[],
    )
    data = service.serialize(graph)
    assert len(data["nodes"]) == 6
    assert any(edge["type"] == "conflicts_with" for edge in data["edges"])
