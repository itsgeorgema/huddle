export type ScenarioParticipant = {
  name: string;
  statement: string;
};

export type Scenario = {
  id: string;
  title: string;
  description: string;
  participant_count: number;
  participants: ScenarioParticipant[];
};

export type Session = {
  id: string;
  title: string;
  description: string;
  status: string;
};

export type Participant = {
  id: string;
  display_name: string;
  statement?: string;
};

export type PipelineStep = {
  name: string;
  status: string;
  latency_ms?: number;
  error?: string;
};

export type GraphResponse = {
  nodes: Array<{ id: string; type: string; label: string; data: Record<string, unknown> }>;
  edges: Array<{ id: string; source: string; target: string; type: string; risk?: number; label?: string }>;
  adjacency: Record<string, string[]>;
};

export type Group = {
  id: string;
  label: string;
  participant_ids: string[];
  risk_score: number;
  diversity_score: number;
  bridge_score: number;
  reasoning: string;
};

export type Brief = {
  group_id: string;
  shared_ground: string[];
  likely_tensions: string[];
  bridge_questions: string[];
  discussion_order: string[];
};

export type RiskRow = {
  pair: string[];
  pair_names: string[];
  risk_score: number;
  reason: string;
};

export type AgentRun = {
  id: string;
  agent_name: string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  latency_ms: number;
  error?: string | null;
};
