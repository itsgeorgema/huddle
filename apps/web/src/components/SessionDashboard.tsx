"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Brief, GraphResponse, Group, Participant, PipelineStep, RiskRow } from "@/lib/types";
import { ConflictGraph } from "./ConflictGraph";

export function SessionDashboard({ sessionId }: { sessionId: string }) {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [risk, setRisk] = useState<RiskRow[]>([]);
  const [live, setLive] = useState<{ event: string; reason: string; intervention: string } | null>(null);
  const [message, setMessage] = useState("They never listen to us and do not care about businesses.");

  useEffect(() => {
    Promise.all([
      api.status(sessionId),
      api.participants(sessionId),
      api.graph(sessionId),
      api.groups(sessionId),
      api.briefs(sessionId),
      api.risk(sessionId)
    ]).then(([status, participantData, graphData, groupData, briefData, riskData]) => {
      setSteps(status.steps);
      setParticipants(participantData);
      setGraph(graphData);
      setGroups(groupData);
      setBriefs(briefData);
      setRisk(riskData);
    });
  }, [sessionId]);

  const participantNames = Object.fromEntries(participants.map((participant) => [participant.id, participant.display_name]));
  const briefsByGroup = Object.fromEntries(briefs.map((brief) => [brief.group_id, brief]));

  async function simulate() {
    setLive(await api.simulateLive(sessionId, [message]));
  }

  return (
    <div className="shell stack">
      <section className="grid three">
        <div className="panel">
          <h2>Pipeline</h2>
          {steps.map((step) => (
            <p key={step.name}>
              <strong>{step.status === "complete" ? "✓" : "•"} {step.name}</strong>{" "}
              <span className="muted">{step.latency_ms ? `${Math.round(step.latency_ms)}ms` : ""}</span>
            </p>
          ))}
        </div>
        <div className="panel">
          <h2>Participants</h2>
          <p className="muted">{participants.length} loaded statements</p>
          {participants.slice(0, 6).map((participant) => (
            <p key={participant.id}>{participant.display_name}</p>
          ))}
        </div>
        <div className="panel">
          <h2>Live Mediation</h2>
          <textarea rows={4} value={message} onChange={(event) => setMessage(event.target.value)} style={{ width: "100%" }} />
          <button className="button" onClick={simulate}>Simulate</button>
          {live && (
            <div>
              <p><strong>{live.event}</strong></p>
              <p className="muted">{live.reason}</p>
              <p>{live.intervention}</p>
            </div>
          )}
        </div>
      </section>

      <section>
        <h2>Conflict Graph</h2>
        <ConflictGraph graph={graph} />
      </section>

      <section className="grid two">
        <div className="panel">
          <h2>Risk Matrix</h2>
          <table>
            <thead>
              <tr><th>Pair</th><th>Risk</th><th>Reason</th></tr>
            </thead>
            <tbody>
              {risk.slice(0, 12).map((row) => (
                <tr key={row.pair.join(":")}>
                  <td>{row.pair_names.join(" ↔ ")}</td>
                  <td>{row.risk_score}</td>
                  <td>{row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h2>Groups</h2>
          <div className="stack">
            {groups.map((group) => (
              <article className="panel" key={group.id}>
                <h3>{group.label}</h3>
                <p className="muted">Risk {group.risk_score} · Diversity {group.diversity_score} · Bridge {group.bridge_score}</p>
                <p>{group.participant_ids.map((id) => participantNames[id] || id).join(", ")}</p>
                <p>{group.reasoning}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="grid two">
        {groups.map((group) => {
          const brief = briefsByGroup[group.id];
          return (
            <article className="panel stack" key={group.id}>
              <h2>{group.label} Mediation Brief</h2>
              {brief ? (
                <>
                  <List title="Shared ground" items={brief.shared_ground} />
                  <List title="Likely tensions" items={brief.likely_tensions} />
                  <List title="Bridge questions" items={brief.bridge_questions} />
                  <List title="Discussion order" items={brief.discussion_order} />
                </>
              ) : (
                <p className="muted">No brief generated.</p>
              )}
            </article>
          );
        })}
      </section>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <strong>{title}</strong>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}
