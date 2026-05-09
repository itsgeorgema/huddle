"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Scenario } from "@/lib/types";

export default function DemoPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState("housing_parking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
            <p className="eyebrow">Scenario intake</p>
            <h1>Demo docket</h1>
            <p>
              Load a civic scenario, run the analysis pipeline, and inspect how Huddle balances conflict, diversity,
              and bridge capacity.
            </p>
          </div>
          <div className="panel dark stack">
            <p className="eyebrow">Analyze a record</p>
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
        </section>

        <section className="section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Available records</p>
              <h2>Choose the public issue to route</h2>
            </div>
            <p>Each card represents a ready-made record with participants, claims, and tensions for the demo pipeline.</p>
          </div>
          {scenarios.length ? (
            <div className="grid scenario-grid">
              {scenarios.map((scenario) => (
                <article className={`panel scenario-card ${selected === scenario.id ? "selected" : ""}`} key={scenario.id}>
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
        </section>
      </div>
    </main>
  );
}
