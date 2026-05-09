"use client";

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

  return (
    <main className="shell stack">
      <section className="panel stack">
        <h1>Huddle</h1>
        <p className="muted">Load a scenario and run the AI deliberation pipeline end to end.</p>
        <div className="row">
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.title}
              </option>
            ))}
          </select>
          <button className="button" onClick={load} disabled={loading || scenarios.length === 0}>
            {loading ? "Running pipeline..." : "Load Scenario and Analyze"}
          </button>
        </div>
        {error && <p style={{ color: "#b42318" }}>{error}</p>}
      </section>
      <section className="grid three">
        {scenarios.map((scenario) => (
          <article className="panel" key={scenario.id}>
            <h3>{scenario.title}</h3>
            <p className="muted">{scenario.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
