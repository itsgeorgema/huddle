from collections import Counter
from itertools import combinations


class ScoringService:
    def pairwise_risk(self, participant_ids: list[str], claim_to_participant: dict[str, str], edges: list[dict]) -> dict[str, dict]:
        risk: dict[str, dict] = {}
        for left, right in combinations(sorted(participant_ids), 2):
            relevant = [
                edge
                for edge in edges
                if {claim_to_participant[edge["source_claim"]], claim_to_participant[edge["target_claim"]]} == {left, right}
            ]
            score = max([edge["risk_score"] for edge in relevant], default=0.12)
            reason = relevant[0]["reason"] if relevant else "No direct high-risk claim conflict detected."
            risk[f"{left}:{right}"] = {
                "risk_score": round(score, 2),
                "reason": reason,
                "recommended_intervention": self.intervention(score),
            }
        return risk

    def intervention(self, score: float) -> str:
        if score >= 0.75:
            return "Begin with shared-ground framing and restatement before rebuttal."
        if score >= 0.5:
            return "Ask participants to separate facts, values, and affected stakeholders."
        return "Use normal discussion order."

    def group_scores(self, participant_ids: list[str], profiles: list[dict], pairwise: dict[str, dict]) -> dict:
        profile_map = {profile["participant_id"]: profile for profile in profiles}
        clusters = [profile_map[p]["viewpoint_cluster"] for p in participant_ids if p in profile_map]
        values = [value for p in participant_ids if p in profile_map for value in profile_map[p]["main_values"]]
        risks = []
        for left, right in combinations(sorted(participant_ids), 2):
            risks.append(pairwise.get(f"{left}:{right}", {}).get("risk_score", 0.12))
        risk_score = sum(risks) / len(risks) if risks else 0.0
        diversity = len(set(clusters)) / max(1, len(clusters))
        coverage = len(set(values)) / max(1, len(values))
        bridge = max([profile_map[p]["bridge_potential"] for p in participant_ids if p in profile_map], default=0)
        minority_penalty = self.minority_isolation_penalty(clusters)
        return {
            "risk_score": round(min(1, risk_score + minority_penalty), 2),
            "diversity_score": round((diversity + coverage) / 2, 2),
            "bridge_score": round(bridge, 2),
            "minority_isolation_penalty": round(minority_penalty, 2),
        }

    def minority_isolation_penalty(self, clusters: list[str]) -> float:
        counts = Counter(clusters)
        if len(clusters) >= 4 and 1 in counts.values() and max(counts.values(), default=0) >= len(clusters) - 1:
            return 0.18
        return 0.0
