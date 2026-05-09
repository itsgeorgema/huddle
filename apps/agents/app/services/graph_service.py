from collections import defaultdict

import networkx as nx


class ConflictGraphService:
    def build(self, participants: list[dict], claims: list[dict], conflict_edges: list[dict], profiles: list[dict]) -> nx.Graph:
        graph = nx.Graph()
        profile_map = {profile["participant_id"]: profile for profile in profiles}
        for participant in participants:
            profile = profile_map.get(participant["id"], {})
            graph.add_node(
                participant["id"],
                type="participant",
                label=participant["display_name"],
                data=profile,
            )
        for claim in claims:
            graph.add_node(
                claim["claim_id"],
                type="claim",
                label=claim["text"][:80],
                data={
                    "claim_type": claim["claim_type"],
                    "stakeholder": claim["stakeholder"],
                    "value": claim["value"],
                },
            )
            graph.add_edge(
                claim["participant_id"],
                claim["claim_id"],
                type="made_claim",
                risk=None,
                label="made claim",
                data={},
            )
            value_id = f"value:{claim['value']}"
            graph.add_node(value_id, type="value", label=claim["value"], data={})
            graph.add_edge(claim["claim_id"], value_id, type="supports", risk=None, label="supports", data={})
        for edge in conflict_edges:
            graph.add_edge(
                edge["source_claim"],
                edge["target_claim"],
                type=edge["edge_type"],
                risk=edge["risk_score"],
                label=edge["conflict_type"],
                data={"reason": edge["reason"]},
            )
        return graph

    def serialize(self, graph: nx.Graph) -> dict:
        nodes = [
            {"id": node, "type": data["type"], "label": data["label"], "data": data.get("data", {})}
            for node, data in graph.nodes(data=True)
        ]
        edges = []
        adjacency: dict[str, list[str]] = defaultdict(list)
        for idx, (source, target, data) in enumerate(graph.edges(data=True)):
            edges.append(
                {
                    "id": f"e{idx}",
                    "source": source,
                    "target": target,
                    "type": data["type"],
                    "risk": data.get("risk"),
                    "label": data.get("label"),
                    "data": data.get("data", {}),
                }
            )
            adjacency[source].append(target)
            adjacency[target].append(source)
        return {"nodes": nodes, "edges": edges, "adjacency": dict(adjacency)}

    def bridge_participants(self, graph: nx.Graph) -> dict[str, float]:
        centrality = nx.betweenness_centrality(graph) if graph.nodes else {}
        return {
            node: round(score, 3)
            for node, score in centrality.items()
            if graph.nodes[node].get("type") == "participant"
        }
