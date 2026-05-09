export type SessionStatus = "draft" | "running" | "complete" | "failed";

export type HuddleSession = {
  id: string;
  title: string;
  description: string;
  status: SessionStatus;
};

export type AnalyzeRequest = {
  group_size: number;
  constraints: Record<string, unknown>;
};

export type RoutingPolicy = {
  strategy: "langgraph_diversity_balancer";
  objectives: string[];
  constraints: Record<string, unknown>;
  group_size: number;
};
