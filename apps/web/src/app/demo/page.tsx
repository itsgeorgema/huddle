"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Scenario } from "@/lib/types";

const PIPELINE_MESSAGES = [
  "Loading scenario into the public record…",
  "Parsing participant statements…",
  "Normalizing tone and language…",
  "Running intake agent…",
  "Extracting structured claims…",
  "Identifying stakeholder positions…",
  "Running conflict classifier agent…",
  "Mapping tension edges across claims…",
  "Building participant viewpoint profiles…",
  "Scoring bridge potential for each participant…",
  "Running diversity load balancer…",
  "Testing pair risk thresholds…",
  "Assembling balanced deliberation rooms…",
  "Running pre-mediation briefing agent…",
  "Generating facilitator notes per group…",
  "Summarizing consensus landscape…",
  "Finalizing session record…",
];

function useReveal(dep?: unknown) {
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
      { threshold: 0.08, rootMargin: "0px 0px -24px 0px" }
    );
    els.forEach((el) => {
      if (!el.hasAttribute("data-visible")) observer.observe(el);
    });
    return () => observer.disconnect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dep]);
}

type Mode = "existing" | "custom";

export default function DemoPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("existing");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState("housing_parking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msgIndex, setMsgIndex] = useState(0);
  const [msgVisible, setMsgVisible] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [conflictText, setConflictText] = useState("");
  const [aiCount, setAiCount] = useState(8);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useReveal(`${mode}-${scenarios.length}`);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!loading) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setMsgIndex(0);
      setMsgVisible(true);
      return;
    }
    intervalRef.current = setInterval(() => {
      setMsgVisible(false);
      setTimeout(() => {
        setMsgIndex((i) => (i + 1) % PIPELINE_MESSAGES.length);
        setMsgVisible(true);
      }, 350);
    }, 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loading]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const session = await api.loadScenario(selected);
      await api.analyze(session.id, 4);
      router.push(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function compose() {
    if (conflictText.trim().length < 10) {
      setError("Describe the conflict in at least 10 characters.");
      return;
    }
    if (!uploadFile && aiCount === 0) {
      setError("Provide at least one persona source: upload personas, generate AI personas, or both.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const session = await api.compose(conflictText.trim(), uploadFile, aiCount);
      await api.analyze(session.id, 4);
      router.push(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const selectedScenario = scenarios.find((scenario) => scenario.id === selected);

  return (
    <main className="app-frame">
      <div className="shell stack">
        <section className="hero compact">
          <div className="hero-copy">
            <p className="eyebrow anim-up" data-anim-index="1">Demo cockpit</p>
            <h1 className="anim-up" data-anim-index="2">Stress-test a decision</h1>
            <p className="anim-up" data-anim-index="3">
              Pick how you want to seed Huddle: walk through a pre-built civic scenario, or describe your own
              conflict and bring real personas, AI-generated personas, or a mix of both.
            </p>
          </div>
        </section>

        <section className="section">
          <div className="section-head" data-reveal>
            <div>
              <p className="eyebrow">Choose your mode</p>
              <h2>How are you bringing your conflict in?</h2>
            </div>
          </div>
          <div className="grid two">
            <article
              className={`panel scenario-card ${mode === "existing" ? "selected" : ""}`}
              onClick={() => setMode("existing")}
              style={{ cursor: "pointer" }}
              data-reveal
              data-step="01"
            >
              <div>
                <p className="eyebrow">{mode === "existing" ? "Selected" : "Option A"}</p>
                <h3>Check an existing conflict</h3>
                <p className="muted" style={{ fontSize: "0.875rem", marginTop: "0.35rem" }}>
                  Pick from pre-built civic scenarios with ready-made participants, claims, and tensions.
                </p>
              </div>
            </article>
            <article
              className={`panel scenario-card ${mode === "custom" ? "selected" : ""}`}
              onClick={() => setMode("custom")}
              style={{ cursor: "pointer" }}
              data-reveal
              data-step="02"
            >
              <div>
                <p className="eyebrow">{mode === "custom" ? "Selected" : "Option B"}</p>
                <h3>Describe your own conflict</h3>
                <p className="muted" style={{ fontSize: "0.875rem", marginTop: "0.35rem" }}>
                  Define the topic, then choose how to populate the room: upload personas, generate AI personas, or mix both.
                </p>
              </div>
            </article>
          </div>
        </section>

        {mode === "existing" && (
          <section className="section">
            <div className="section-head" data-reveal>
              <div>
                <p className="eyebrow">Pre-built scenarios</p>
                <h2>Choose a public issue to route</h2>
              </div>
              <p>
                Each card represents a ready-made record with participants, claims, and tensions for the demo pipeline.
              </p>
            </div>

            <div className="panel dark stack anim-up" data-anim-index="4">
              <p className="eyebrow">Analyze a record</p>
              {loading ? (
                <div className="pipeline-log">
                  <div className="pipeline-log-spinner" />
                  <p
                    className="pipeline-log-msg"
                    style={{ opacity: msgVisible ? 1 : 0 }}
                  >
                    {PIPELINE_MESSAGES[msgIndex]}
                  </p>
                </div>
              ) : (
                <>
                  <label className="stack tight">
                    <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Scenario</span>
                    <select value={selected} onChange={(event) => setSelected(event.target.value)}>
                      {scenarios.map((scenario) => (
                        <option key={scenario.id} value={scenario.id}>
                          {scenario.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  {selectedScenario?.description && (
                    <p className="muted" style={{ fontSize: "0.875rem" }}>
                      {selectedScenario.description}
                    </p>
                  )}
                  {!selectedScenario && (
                    <p className="muted" style={{ fontSize: "0.875rem" }}>Choose a scenario to start the pipeline.</p>
                  )}
                </>
              )}
              <button className="button" onClick={load} disabled={loading || scenarios.length === 0}>
                {loading ? "Pipeline running…" : "Load and analyze"}
              </button>
              {error && <p className="error-state">{error}</p>}
            </div>

            {scenarios.length ? (
              <div className="grid scenario-grid">
                {scenarios.map((scenario, i) => (
                  <article
                    className={`panel scenario-card ${selected === scenario.id ? "selected" : ""}`}
                    key={scenario.id}
                    data-reveal
                    data-step={String(i + 1).padStart(2, "0")}
                  >
                    <div>
                      <p className="eyebrow">{selected === scenario.id ? "Selected" : "Scenario"}</p>
                      <h3>{scenario.title}</h3>
                      <p className="muted" style={{ fontSize: "0.875rem", marginTop: "0.35rem" }}>
                        {scenario.description}
                      </p>
                    </div>
                    <button
                      className="button secondary"
                      onClick={() => setSelected(scenario.id)}
                      style={{ marginTop: "0.85rem" }}
                    >
                      {selected === scenario.id ? "Active record" : "Select record"}
                    </button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="skeleton stack" data-reveal>
                <div className="skeleton-line short" />
                <div className="skeleton-line" />
                <div className="skeleton-line medium" />
              </div>
            )}
          </section>
        )}

        {mode === "custom" && (
          <section className="section">
            <div className="section-head" data-reveal>
              <div>
                <p className="eyebrow">Define your room</p>
                <h2>Bring your own conflict</h2>
              </div>
              <p>
                Describe the topic, then pick your personas. Upload a CSV, generate diverse AI personas, or mix
                both. When both are provided, the AI fills viewpoint gaps left by your real personas instead of
                duplicating them.
              </p>
            </div>

            <div className="panel dark stack anim-up" data-anim-index="4">
              <p className="eyebrow">Compose a room</p>
              {loading ? (
                <div className="pipeline-log">
                  <div className="pipeline-log-spinner" />
                  <p
                    className="pipeline-log-msg"
                    style={{ opacity: msgVisible ? 1 : 0 }}
                  >
                    {PIPELINE_MESSAGES[msgIndex]}
                  </p>
                </div>
              ) : (
                <>
                  <label className="stack tight">
                    <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Conflict description</span>
                    <textarea
                      rows={5}
                      placeholder="E.g., 'Should our school ban phones during class hours?' Provide enough context that the LLM understands the stakeholders involved."
                      value={conflictText}
                      onChange={(event) => setConflictText(event.target.value)}
                    />
                  </label>
                  <label className="stack tight">
                    <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Upload personas (optional CSV)</span>
                    <input
                      type="file"
                      accept=".csv,text/csv"
                      onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                    />
                  </label>
                  {uploadFile && (
                    <p className="muted" style={{ fontSize: "0.875rem" }}>
                      Selected: <strong>{uploadFile.name}</strong>
                    </p>
                  )}
                  <label className="stack tight">
                    <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>AI personas (0–15, set to 0 to skip)</span>
                    <input
                      type="number"
                      min={0}
                      max={15}
                      value={aiCount}
                      onChange={(event) => setAiCount(Number(event.target.value))}
                    />
                  </label>
                  <p className="muted" style={{ fontSize: "0.875rem" }}>
                    Provide at least one persona source. CSV columns: <code>display_name</code>, <code>statement</code>.
                    Other columns are accepted but ignored. Empty fields are skipped.
                  </p>
                </>
              )}
              <button
                className="button"
                onClick={compose}
                disabled={loading || conflictText.trim().length < 10 || (!uploadFile && aiCount === 0)}
              >
                {loading ? "Pipeline running…" : "Compose and analyze"}
              </button>
              {error && <p className="error-state">{error}</p>}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
