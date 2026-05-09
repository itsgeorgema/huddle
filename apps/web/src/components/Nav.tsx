import Link from "next/link";

export function Nav() {
  return (
    <nav className="nav-bar">
      <div className="nav-inner">
        <Link href="/" className="nav-brand">
          <span className="nav-brand-dot" aria-hidden="true" />
          Huddle
        </Link>
        <div className="nav-links">
          <Link className="nav-link" href="/">Process</Link>
          <Link className="nav-link" href="/demo">Demo</Link>
        </div>
        <Link className="nav-cta" href="/demo">Open docket</Link>
      </div>
    </nav>
  );
}
