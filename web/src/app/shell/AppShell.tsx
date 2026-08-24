import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { JaneDock } from './JaneDock';
import './AppShell.css';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  /** match prefix for active state (defaults to `to`) */
  match?: string;
}

/** Dominant STITCH shell: wide labeled sidebar. Domain-grouped nav (plan §7). */
const NAV: NavItem[] = [
  { to: '/workspace', icon: 'grid_view', label: 'Workspace' },
  { to: '/intake', icon: 'database', label: 'Datasets' },
  { to: '/data-studio', icon: 'analytics', label: 'Data Studio' },
  { to: '/jobs/job_running', icon: 'format_list_bulleted', label: 'Jobs', match: '/jobs' },
  { to: '/models', icon: 'deployed_code', label: 'Models' },
  { to: '/deployments', icon: 'rocket_launch', label: 'Deployments' },
  { to: '/agents', icon: 'smart_toy', label: 'Agents' },
  { to: '/admin/access-control', icon: 'settings', label: 'Admin', match: '/admin' },
];

export function AppShell() {
  const { pathname } = useLocation();

  return (
    <div className="shell">
      {/* ── Left sidebar ───────────────────────────────────────────────── */}
      <aside className="shell__side">
        <div className="shell__brand">
          <NavLink to="/" className="shell__brand-name">
            AIConnex
          </NavLink>
          <div className="shell__project">
            <span className="shell__project-name">Project Alpha</span>
            <span className="shell__project-env label-mono">PRODUCTION ENVIRONMENT</span>
          </div>
        </div>

        <button type="button" className="shell__new-exp label-mono">
          NEW EXPERIMENT
          <span className="material-symbols-outlined">add</span>
        </button>

        <nav className="shell__nav" aria-label="Primary">
          {NAV.map((item) => {
            const prefix = item.match ?? item.to;
            const isActive =
              prefix === '/' ? pathname === '/' : pathname.startsWith(prefix);
            return (
              <NavLink
                key={item.label}
                to={item.to}
                className={`shell__nav-item label-mono${isActive ? ' shell__nav-item--active' : ''}`}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      {/* ── Center column: top bar + main + footer ─────────────────────── */}
      <div className="shell__center">
        <header className="shell__topbar">
          <label className="shell__search">
            <span className="material-symbols-outlined">search</span>
            <input placeholder="Search..." aria-label="Search" />
          </label>
          <div className="shell__topbar-actions">
            <span className="shell__user">Jane Agent</span>
            <button type="button" className="shell__icon-btn" title="Notifications">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button type="button" className="shell__icon-btn" title="Account">
              <span className="material-symbols-outlined">account_circle</span>
            </button>
          </div>
        </header>

        <main className="shell__main">
          <Outlet />
        </main>

        <footer className="shell__footer label-mono">
          <span className="shell__footer-status">
            <span className="shell__footer-dot" /> System Status: API Operational
          </span>
          <span className="shell__footer-meta">
            v2.4.1-stable <a href="#support">Support</a>
          </span>
        </footer>
      </div>

      <JaneDock />
    </div>
  );
}
