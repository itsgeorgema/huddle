# Routing Algorithm

The routing engine is invoked by the LangGraph `diversity_load_balancer` agent node.

Inputs:

- participants
- participant profiles
- pairwise conflict risk
- target group size
- routing constraints

Process:

1. Cluster participants by dominant viewpoint.
2. Sort each cluster by bridge potential.
3. Round-robin participants from different clusters across groups.
4. Score each group for conflict risk, diversity, bridge coverage, and minority isolation.
5. Persist explainable group reasoning.

The current implementation favors transparent heuristics over black-box optimization. It can later be replaced with OR-Tools or scipy optimization while preserving the API contract. If routing becomes latency-sensitive or high-throughput, this module is the extraction point for a Go routing service.
