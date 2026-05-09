from collections import Counter, defaultdict

from app.agents.base import Agent


class ParticipantProfilerAgent(Agent):
    name = "participant_profiling"

    async def run(self, payload: dict) -> dict:
        claims = payload["claims"]
        edges = payload["conflict_edges"]
        by_participant: dict[str, list[dict]] = defaultdict(list)
        edge_counts: Counter[str] = Counter()
        for claim in claims:
            by_participant[claim["participant_id"]].append(claim)
        claim_to_participant = {claim["claim_id"]: claim["participant_id"] for claim in claims}
        for edge in edges:
            edge_counts[claim_to_participant[edge["source_claim"]]] += edge["risk_score"]
            edge_counts[claim_to_participant[edge["target_claim"]]] += edge["risk_score"]
        profiles = []
        for participant_id, participant_claims in by_participant.items():
            values = [claim["value"] for claim in participant_claims]
            value_counts = Counter(values)
            cluster = value_counts.most_common(1)[0][0].replace(" ", "_")
            value_diversity = len(set(values)) / max(1, len(values))
            risk = min(1.0, edge_counts[participant_id] / max(1, len(participant_claims) * 3))
            bridge_score = round(min(0.95, 0.25 + value_diversity * 0.35 + (0.22 if 0.25 < risk < 0.75 else 0)), 2)
            profiles.append(
                {
                    "participant_id": participant_id,
                    "viewpoint_cluster": cluster,
                    "main_values": list(value_counts.keys()),
                    "claims": [claim["claim_id"] for claim in participant_claims],
                    "conflict_risk": round(risk, 2),
                    "bridge_potential": bridge_score,
                }
            )
        return {"profiles": profiles}
