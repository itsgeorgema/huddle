"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Brief, GraphResponse, Group, Participant, PipelineStep, RiskRow } from "@/lib/types";
import { ConflictGraph } from "./ConflictGraph";

const stages = ["Intake", "Claim extraction", "Conflict graph", "Load balancing", "Mediation briefs"];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll<HTMLElement>("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.setAttribute("data-visible", "");
            observer.unobserve(e.target);
          }
        }),
      { threshold: 0.06, rootMargin: "0px 0px -24px 0px" }
    );
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
}

export function SessionDashboard({ sessionId }: { sessionId: string }) {
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [risk, setRisk] = useState<RiskRow[]>([]);
  const [live, setLive] = useState<{ event: string; reason: string; intervention: string } | null>(null);
  const [message, setMessage] = useState("They never listen to us and do not care about businesses.");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);

  useReveal();

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    Promise.all([
      api.status(sessionId),
      api.participants(sessionId),
      api.graph(sessionId),
      api.groups(sessionId),
      api.briefs(sessionId),
      api.risk(sessionId)
    ])
      .then(([status, participantData, graphData, groupData, briefData, riskData]) => {
        if (!active) return;
        setSteps(status.steps);
        setParticipants(participantData);
        setGraph(graphData);
        setGroups(groupData);
        setBriefs(briefData);
        setRisk(riskData);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unable to load session data.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [sessionId]);

  const participantNames = useMemo(
    () => Object.fromEntries(participants.map((p) => [p.id, p.display_name])),
    [participants]
  );
  const briefsByGroup = useMemo(() => Object.fromEntries(briefs.map((b) => [b.group_id, b])), [briefs]);
  const conflictEdges = graph?.edges.filter((e) => e.type === "conflicts_with").length ?? 0;
  const averageRisk = risk.length ? risk.reduce((t, r) => t + r.risk_score, 0) / risk.length : 0;
  const completedSteps = steps.filter((s) => s.status === "complete").length;
  const bridgeAverage = groups.length ? groups.reduce((t, g) => t + g.bridge_score, 0) / groups.length : 0;

  async function simulate() {
    setSimulating(true);
    setLive(null);
    try {
      setLive(await api.simulateLive(sessionId, [message]));
    } finally {
      setSimulating(false);
    }
  }

  return (
    <main className="app-frame">
      <div className="shell stack">
        {/* Hero */}
        <section className="hero compact">
          <div className="hero-copy">
            <p className="eyebrow anim-up" data-anim-index="1">Public deliberation docket</p>
            <h1 className="anim-up" data-anim-index="2">Huddle</h1>
            <p className="anim-up" data-anim-index="3">
              Conflict-aware load balancing for civic discussions, with the analysis trail visible from intake to
              group assignment.
            </p>
            <div className="row anim-up" data-anim-index="4">
              <a className="button" href="#routing">Review group routing</a>
              <a className="button secondary" href="#graph">Inspect conflict graph</a>
            </div>
          </div>

          <div className="panel dark stack anim-up" data-anim-index="5">
            <p className="eyebrow">Session record</p>
            <div className="stat-grid">
              <Metric value={participants.length} label="Participants" />
              <Metric value={conflictEdges} label="Conflict edges" />
              <Metric value={groups.length} label="Balanced groups" />
              <Metric value={formatScore(averageRisk)} label="Mean risk" />
            </div>
          </div>
        </section>

        {error && <div className="error-state" data-reveal>{error}</div>}

        {/* Main grid */}
        <section className="grid dashboard-grid">
          <aside className="stack">
            <div className="panel stack" data-reveal>
              <div>
                <p className="eyebrow">Analysis process</p>
                <h2>Pipeline record</h2>
                <p className="muted" style={{ fontSize: "0.875rem" }}>
                  Each step is surfaced so users can see how raw statements become claims, conflicts, and groups.
                </p>
              </div>
              {loading ? <Skeleton count={5} /> : <Pipeline steps={steps} completedSteps={completedSteps} />}
            </div>

            <div className="panel stack" data-reveal>
              <div className="spread">
                <div>
                  <p className="eyebrow">Participants</p>
                  <h2>Loaded statements</h2>
                </div>
                <span className="badge">{participants.length} records</span>
              </div>
              {loading ? (
                <Skeleton count={6} />
              ) : participants.length ? (
                <div className="participant-list">
                  {participants.slice(0, 8).map((participant, index) => (
                    <div className="participant-chip" key={participant.id}>
                      <span className="node-dot">{index + 1}</span>
                      <span>{participant.display_name}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">No participants are attached to this session.</div>
              )}
            </div>
          </aside>

          <section className="stack">
            <div className="panel raised stack" data-reveal>
              <div className="section-head" style={{ marginTop: 0, marginBottom: "0.25rem" }}>
                <div>
                  <p className="eyebrow">Decision trail</p>
                  <h2>How the balancing process reads the room</h2>
                </div>
                <span className="badge seal">Neutral routing</span>
              </div>
              <div className="timeline">
                {stages.map((stage, index) => (
                  <div className="timeline-item" key={stage}>
                    <span className="timeline-dot" />
                    <div className="timeline-copy">
                      <h3>{stage}</h3>
                      <p className="muted" style={{ fontSize: "0.875rem" }}>{stageDescription(index)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel stack" data-reveal>
              <div className="spread">
                <div>
                  <p className="eyebrow">Live mediation</p>
                  <h2>Test an intervention</h2>
                </div>
                <span className="badge">Session {sessionId.slice(0, 8)}</span>
              </div>
              <label className="stack tight">
                <span className="muted" style={{ fontSize: "0.875rem" }}>Incoming room message</span>
                <textarea rows={4} value={message} onChange={(event) => setMessage(event.target.value)} />
              </label>
              <button className="button" onClick={simulate} disabled={simulating || !message.trim()}>
                {simulating ? "Reviewing message…" : "Simulate intervention"}
              </button>
              {live && (
                <div className="panel" data-reveal>
                  <p className="eyebrow">{live.event}</p>
                  <h3>{live.intervention}</h3>
                  <p className="muted" style={{ fontSize: "0.875rem", marginTop: "0.35rem" }}>{live.reason}</p>
                </div>
              )}
            </div>
          </section>
        </section>

        {/* Conflict graph */}
        <section className="section" id="graph" data-reveal>
          <div className="section-head">
            <div>
              <p className="eyebrow">Conflict graph</p>
              <h2>Claims, participants, and tension edges</h2>
            </div>
            <p>The graph uses distinct node treatments so the source of each conflict is easier to discover.</p>
          </div>
          <ConflictGraph graph={graph} />
        </section>

        {/* Risk + groups */}
        <section className="section grid two" id="routing">
          <div data-reveal>
            <div className="section-head">
              <div>
                <p className="eyebrow">Risk matrix</p>
                <h2>Pairs requiring facilitation</h2>
              </div>
            </div>
            <div className="panel">
              {loading ? (
                <Skeleton count={8} />
              ) : risk.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>Pair</th>
                      <th>Risk</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {risk.slice(0, 12).map((row) => (
                      <tr key={row.pair.join(":")}>
                        <td>{row.pair_names.join(" / ")}</td>
                        <td>
                          <span className="risk-score">{formatScore(row.risk_score)}</span>
                        </td>
                        <td>{row.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">No pairwise risk rows have been generated.</div>
              )}
            </div>
          </div>

          <div data-reveal>
            <div className="section-head">
              <div>
                <p className="eyebrow">Group assignments</p>
                <h2>Balanced rooms</h2>
              </div>
              <span className="badge">Bridge avg {formatScore(bridgeAverage)}</span>
            </div>
            <div className="stack">
              {loading ? (
                <Skeleton count={5} />
              ) : groups.length ? (
                groups.map((group) => (
                  <article className="panel group-card" key={group.id}>
                    <div className="spread">
                      <h3>{group.label}</h3>
                      <span className="badge">{group.participant_ids.length} participants</span>
                    </div>
                    <div className="score-row">
                      <Score label="Risk" value={group.risk_score} />
                      <Score label="Diversity" value={group.diversity_score} />
                      <Score label="Bridge" value={group.bridge_score} />
                    </div>
                    <p style={{ fontSize: "0.875rem" }}>
                      {group.participant_ids.map((id) => participantNames[id] || id).join(", ")}
                    </p>
                    <p className="muted" style={{ fontSize: "0.875rem" }}>{group.reasoning}</p>
                  </article>
                ))
              ) : (
                <div className="empty-state">No group assignments are available yet.</div>
              )}
            </div>
          </div>
        </section>

        {/* Mediation briefs */}
        <section className="section" data-reveal>
          <div className="section-head">
            <div>
              <p className="eyebrow">Mediation briefs</p>
              <h2>Facilitator-ready room notes</h2>
            </div>
            <p>Briefs translate graph analysis into neutral discussion prompts and ordering.</p>
          </div>
          <div className="grid group-grid">
            {groups.map((group) => {
              const brief = briefsByGroup[group.id];
              return (
                <article className="panel stack" key={group.id}>
                  <div>
                    <p className="eyebrow">{group.label}</p>
                    <h2>Mediation brief</h2>
                  </div>
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
          </div>
        </section>
      </div>
    </main>
  );
}

function Pipeline({ steps, completedSteps }: { steps: PipelineStep[]; completedSteps: number }) {
  if (!steps.length) {
    return <div className="empty-state">No pipeline status has been reported for this session.</div>;
  }

  return (
    <div className="process-list">
      {steps.map((step, index) => (
        <div className={`process-step ${step.status === "complete" ? "complete" : "pending"}`} key={step.name}>
          <span className="process-index">{step.status === "complete" ? "OK" : index + 1}</span>
          <div>
            <strong style={{ fontSize: "0.9rem" }}>{step.name}</strong>
            {step.error && <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.2rem" }}>{step.error}</p>}
          </div>
          <span className="latency">{step.latency_ms ? `${Math.round(step.latency_ms)}ms` : "queued"}</span>
        </div>
      ))}
      <p className="muted" style={{ fontSize: "0.8rem" }}>
        {completedSteps} of {steps.length} stages complete.
      </p>
    </div>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-box">
      <strong>{formatScore(value)}</strong>
      <span className="muted" style={{ fontSize: "0.78rem" }}>{label}</span>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <strong style={{ fontSize: "0.875rem" }}>{title}</strong>
      <ul className="brief-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function Skeleton({ count }: { count: number }) {
  return (
    <div className="stack tight skeleton" aria-label="Loading">
      {Array.from({ length: count }).map((_, index) => (
        <div
          className={`skeleton-line ${index % 3 === 0 ? "short" : index % 2 === 0 ? "medium" : ""}`}
          key={index}
        />
      ))}
    </div>
  );
}

function formatScore(value: number) {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
}

function stageDescription(index: number) {
  return [
    "Statements enter the public record with speaker context preserved.",
    "Claims are extracted and normalized before graph construction.",
    "Edges reveal agreement, tension, and topic proximity across the room.",
    "The balancer tests risk, viewpoint diversity, and bridge capacity.",
    "Each group receives facilitation notes for a more structured discussion."
  ][index];
}
