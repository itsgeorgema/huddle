import Link from "next/link";

export default function Home() {
  return (
    <main className="shell stack">
      <section className="panel stack">
        <div>
          <h1>Huddle</h1>
          <p className="muted">Conflict-aware deliberation load balancing for structured civic discussion.</p>
        </div>
        <Link className="button" href="/demo">
          Open demo cockpit
        </Link>
      </section>
    </main>
  );
}
