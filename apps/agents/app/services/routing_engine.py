from collections import defaultdict

from app.services.scoring_service import ScoringService


class RoutingEngine:
    def __init__(self) -> None:
        self.scoring = ScoringService()

    def route(
        self,
        participants: list[dict],
        profiles: list[dict],
        pairwise_risk: dict[str, dict],
        group_size: int,
        constraints: dict | None = None,
    ) -> list[dict]:
        constraints = constraints or {}
        profile_map = {profile["participant_id"]: profile for profile in profiles}
        by_cluster: dict[str, list[str]] = defaultdict(list)
        for participant in participants:
            profile = profile_map.get(participant["id"])
            cluster = profile["viewpoint_cluster"] if profile else "unclassified"
            by_cluster[cluster].append(participant["id"])
        for ids in by_cluster.values():
            ids.sort(key=lambda pid: profile_map.get(pid, {}).get("bridge_potential", 0), reverse=True)

        groups: list[list[str]] = []
        total = len(participants)
        target_count = max(1, (total + group_size - 1) // group_size)
        for _ in range(target_count):
            groups.append([])

        cluster_items = sorted(by_cluster.items(), key=lambda item: len(item[1]), reverse=True)
        group_clusters: list[set[str]] = [set() for _ in groups]
        for cluster, ids in cluster_items:
            for participant_id in ids:
                candidates = [
                    idx
                    for idx, group in enumerate(groups)
                    if len(group) < group_size and cluster not in group_clusters[idx]
                ]
                if not candidates:
                    candidates = [idx for idx, group in enumerate(groups) if len(group) < group_size]
                if not candidates:
                    groups.append([])
                    group_clusters.append(set())
                    candidates = [len(groups) - 1]
                target = min(candidates, key=lambda idx: len(groups[idx]))
                groups[target].append(participant_id)
                group_clusters[target].add(cluster)

        groups = [group for group in groups if group]
        routed = []
        for index, participant_ids in enumerate(groups, start=1):
            scores = self.scoring.group_scores(participant_ids, profiles, pairwise_risk)
            profile_clusters = sorted({profile_map[p]["viewpoint_cluster"] for p in participant_ids if p in profile_map})
            routed.append(
                {
                    "id": f"g{index}",
                    "label": f"Group {chr(64 + index)}",
                    "participant_ids": participant_ids,
                    **scores,
                    "reasoning": self._reasoning(profile_clusters, scores, constraints),
                }
            )
        return routed

    def _reasoning(self, clusters: list[str], scores: dict, constraints: dict) -> str:
        risk = "manageable" if scores["risk_score"] <= constraints.get("max_group_risk", 0.75) else "elevated"
        return (
            f"Balances {', '.join(clusters) or 'available'} viewpoints with {risk} conflict risk, "
            f"diversity score {scores['diversity_score']}, and bridge score {scores['bridge_score']}."
        )
