"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Scenario } from "@/lib/types";

type Mode = "existing" | "custom";

export default function DemoPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("existing");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState("housing_parking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [conflictText, setConflictText] = useState("");
  const [aiCount, setAiCount] = useState(8);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch((err) => setError(err.message));
  }, []);

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
      setError("Pick at least one source: upload personas, generate AI personas, or both.");
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
        <div className="row">
          <Link href="/" className="button secondary" style={{ textDecoration: "none" }}>
            ← Back to home
          </Link>
        </div>

        <section className="hero compact">
          <div className="hero-copy">
            <p className="eyebrow">Demo cockpit</p>
            <h1>Stress-test a decision</h1>
            <p>
              Pick how you want to seed Huddle: walk through a pre-built civic scenario, or describe your own
              conflict and bring real personas, AI-generated personas, or both.
            </p>
          </div>
        </section>

        <section className="section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Choose your mode</p>
              <h2>How are you bringing your conflict in?</h2>
            </div>
          </div>
          <div className="grid two">
            <ModeCard
              active={mode === "existing"}
              eyebrow="Option A"
              title="Check an existing conflict"
              description="Pick from pre-built civic scenarios with ready-made participants, claims, and tensions."
              onClick={() => setMode("existing")}
            />
            <ModeCard
              active={mode === "custom"}
              eyebrow="Option B"
              title="Describe your own conflict"
              description="Define the topic, then choose how to populate the room: upload your own personas, generate diverse AI personas, or mix both."
              onClick={() => setMode("custom")}
            />
          </div>
        </section>

        {mode === "existing" && (
          <section className="section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Pre-built scenarios</p>
                <h2>Choose a public issue to route</h2>
              </div>
              <p>Each scenario is a ready-made record with participants, claims, and tensions baked in.</p>
            </div>
            <div className="stack" style={{ gap: "32px" }}>
              <div className="panel dark stack">
                <label className="stack tight">
                  <span>Scenario</span>
                  <select value={selected} onChange={(event) => setSelected(event.target.value)}>
                    {scenarios.map((scenario) => (
                      <option key={scenario.id} value={scenario.id}>
                        {scenario.title}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="muted">{selectedScenario?.description || "Choose a scenario to start the pipeline."}</p>
                <button className="button" onClick={load} disabled={loading || scenarios.length === 0}>
                  {loading ? "Running pipeline..." : "Load and analyze"}
                </button>
                {error && <p className="error-state">{error}</p>}
              </div>
              {scenarios.length ? (
                <div className="grid scenario-grid">
                  {scenarios.map((scenario) => (
                    <article
                      className={`panel scenario-card ${selected === scenario.id ? "selected" : ""}`}
                      key={scenario.id}
                    >
                      <div>
                        <p className="eyebrow">{selected === scenario.id ? "Selected" : "Scenario"}</p>
                        <h3>{scenario.title}</h3>
                        <p className="muted">{scenario.description}</p>
                      </div>
                      <button className="button secondary" onClick={() => setSelected(scenario.id)}>
                        Select record
                      </button>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="skeleton stack">
                  <div className="skeleton-line short" />
                  <div className="skeleton-line" />
                  <div className="skeleton-line medium" />
                </div>
              )}
            </div>
          </section>
        )}

        {mode === "custom" && (
          <section className="section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Define your room</p>
                <h2>Bring your own conflict</h2>
              </div>
              <p>
                Describe the topic, then pick your personas. Upload a CSV, generate diverse AI personas, or mix
                both — when both are provided, the AI tries to fill viewpoint gaps left by your real personas.
              </p>
            </div>
            <div className="panel dark stack">
              <label className="stack tight">
                <span>Conflict description</span>
                <textarea
                  rows={5}
                  placeholder="E.g., 'Should our school ban phones during class hours?' Provide enough context that the LLM understands the stakeholders involved."
                  value={conflictText}
                  onChange={(event) => setConflictText(event.target.value)}
                />
              </label>

              <label className="stack tight">
                <span>Upload personas (optional CSV)</span>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                />
              </label>
              {uploadFile && (
                <p className="muted">
                  Selected: <strong>{uploadFile.name}</strong>
                </p>
              )}

              <label className="stack tight">
                <span>AI personas (0–15, set to 0 to skip)</span>
                <input
                  type="number"
                  min={0}
                  max={15}
                  value={aiCount}
                  onChange={(event) => setAiCount(Number(event.target.value))}
                />
              </label>

              <p className="muted">
                Provide at least one persona source. CSV columns: <code>display_name</code>, <code>statement</code>.
                Other columns are accepted but ignored. Empty fields are skipped.
              </p>

              <button
                className="button"
                onClick={compose}
                disabled={loading || conflictText.trim().length < 10 || (!uploadFile && aiCount === 0)}
              >
                {loading ? "Running pipeline..." : "Compose and analyze"}
              </button>
              {error && <p className="error-state">{error}</p>}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function ModeCard({
  active,
  eyebrow,
  title,
  description,
  onClick
}: {
  active: boolean;
  eyebrow: string;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <article
      className={`panel scenario-card ${active ? "selected" : ""}`}
      onClick={onClick}
      style={{ cursor: "pointer" }}
    >
      <div>
        <p className="eyebrow">{active ? "Selected" : eyebrow}</p>
        <h3>{title}</h3>
        <p className="muted">{description}</p>
      </div>
    </article>
  );
}
