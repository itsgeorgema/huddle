import type { Brief, GraphResponse, Group, Participant, PipelineStep, RiskRow, Scenario, Session } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  scenarios: () => request<Scenario[]>("/api/demo/scenarios"),
  loadScenario: (id: string) => request<Session>(`/api/demo/scenarios/${id}/load`, { method: "POST" }),
  analyze: (sessionId: string, groupSize = 4) =>
    request<{ status: string }>(`/api/sessions/${sessionId}/analyze`, {
      method: "POST",
      body: JSON.stringify({
        group_size: groupSize,
        constraints: { protect_minority_views: true, require_bridge_participants: true, max_group_risk: 0.75 }
      })
    }),
  status: (sessionId: string) => request<{ status: string; steps: PipelineStep[] }>(`/api/sessions/${sessionId}/analysis/status`),
  participants: (sessionId: string) => request<Participant[]>(`/api/sessions/${sessionId}/participants`),
  graph: (sessionId: string) => request<GraphResponse>(`/api/sessions/${sessionId}/graph`),
  groups: (sessionId: string) => request<Group[]>(`/api/sessions/${sessionId}/groups`),
  briefs: (sessionId: string) => request<Brief[]>(`/api/sessions/${sessionId}/mediation-briefs`),
  risk: (sessionId: string) => request<RiskRow[]>(`/api/sessions/${sessionId}/risk-matrix`),
  simulateLive: (sessionId: string, messages: string[]) =>
    request<{ event: string; reason: string; intervention: string }>(`/api/sessions/${sessionId}/simulate-live`, {
      method: "POST",
      body: JSON.stringify({ messages })
    })
};
