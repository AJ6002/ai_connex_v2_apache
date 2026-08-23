import { NavLink, Outlet } from 'react-router-dom';
import './AdminLayout.css';

const TABS = [
  { to: '/admin/access-control', label: 'Access Control' },
  { to: '/admin/audit-logs', label: 'Audit Logs' },
  { to: '/admin/usage-quotas', label: 'Usage & Quotas' },
  { to: '/admin/workspace', label: 'Workspace Config' },
  { to: '/admin/system-states', label: 'System States' },
];

/** Shared Admin sub-nav — breadcrumb + tab bar, faithful to the STITCH admin screens. */
export function AdminLayout() {
  return (
    <div className="adminl">
      <nav className="adminl__tabs">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) => `adminl__tab${isActive ? ' adminl__tab--active' : ''}`}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
