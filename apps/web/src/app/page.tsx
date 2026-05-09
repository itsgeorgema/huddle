import Link from "next/link";

export default function Home() {
  return (
    <main className="app-frame">
      <div className="shell narrow">
        <section className="hero">
          <div className="hero-copy stack">
            <p className="eyebrow">Civic deliberation infrastructure</p>
            <h1>Huddle</h1>
            <p>
              A neutral routing cockpit for public discussion: extract claims, detect tensions, map the graph, and
              assemble balanced rooms without hiding the reasoning trail.
            </p>
            <div className="row">
              <Link className="button" href="/demo">
                Open demo cockpit
              </Link>
              <a className="button secondary" href="#process">
                View process
              </a>
            </div>
          </div>
          <div className="hero-docket">
            <div className="document-stack">
              <div className="docket-card secondary">
                <p className="eyebrow">Conflict graph</p>
                <div className="docket-line" />
                <p className="muted">Participant nodes connect through claim edges, topic proximity, and tension weight.</p>
                <div className="docket-line" />
                <p className="muted">Grouping rules preserve viewpoint diversity while lowering room volatility.</p>
              </div>
              <div className="docket-card">
                <div className="spread">
                  <p className="eyebrow">Routing order</p>
                  <span className="badge">Public record</span>
                </div>
                <h2>Load balancing docket</h2>
                <div className="stat-grid">
                  <div className="stat">
                    <strong>04</strong>
                    <span>Analysis stages</span>
                  </div>
                  <div className="stat">
                    <strong>12</strong>
                    <span>Risk checks</span>
                  </div>
                  <div className="stat">
                    <strong>03</strong>
                    <span>Balanced rooms</span>
                  </div>
                  <div className="stat">
                    <strong>0.42</strong>
                    <span>Target risk</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="process">
          <div className="section-head">
            <div>
              <p className="eyebrow">Visible process</p>
              <h2>From hearing record to balanced rooms</h2>
            </div>
            <p>Huddle makes the route discoverable so facilitators can audit every major choice.</p>
          </div>
          <div className="grid scenario-grid">
            {[
              ["Extract", "Convert public comments into normalized claims and speaker context."],
              ["Map", "Build a conflict graph that shows agreement, friction, and topic adjacency."],
              ["Balance", "Score pair risk, diversity, and bridge capacity before assigning groups."]
            ].map(([title, description]) => (
              <article className="panel scenario-card" key={title}>
                <p className="eyebrow">{title}</p>
                <h3>{description}</h3>
                <span className="badge">Audit-ready</span>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
