import { Button } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useCredentials, usePersonnel, useWorkspaceInfo } from '@/entities/workspace/hooks';
import './AdminView.css';

/** Access Control — faithful to STITCH-Design/ai_connex_admin_access_control. */
export function AdminView() {
  const { data: workspace } = useWorkspaceInfo();
  const { data: personnel = [], isLoading, isError, error } = usePersonnel();
  const { data: credentials = [] } = useCredentials();
  const q = workspace?.quotas;

  return (
    <div className="adm">
      <header className="adm__header">
        <div>
          <h1 className="adm__title">Access Control</h1>
          <p className="adm__sub">Manage users, roles, and API keys across the organization.</p>
        </div>
        <div className="adm__header-actions">
          <Button variant="secondary">Export Log</Button>
          <Button variant="primary" rightIcon={<span className="material-symbols-outlined">upload</span>}>Add User</Button>
        </div>
      </header>

      <div className="adm__grid">
        <section className="adm__panel">
          <div className="adm__panel-head">
            <span className="label-mono">ACTIVE PERSONNEL</span>
            <span className="label-mono adm__panel-count">Total: {personnel.length}</span>
          </div>
          <AsyncState isLoading={isLoading} isError={isError} error={error}>
            <table className="adm__table">
              <thead><tr><th>NAME / ID</th><th>ROLE</th><th>STATUS</th><th>LAST ACTIVE</th><th /></tr></thead>
              <tbody>
                {personnel.map((u) => (
                  <tr key={u.userId}>
                    <td>
                      <span className="adm__user-name">{u.name}</span>
                      <span className="adm__user-id">{u.userId}</span>
                    </td>
                    <td className="adm__role">{u.role}</td>
                    <td className={u.status === 'ACTIVE' ? 'adm__status--active' : ''}>{u.status === 'ACTIVE' ? 'Active' : 'Inactive'}</td>
                    <td>{u.lastActive}</td>
                    <td><button type="button" className="adm__more" aria-label="More actions"><span className="material-symbols-outlined">more_vert</span></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </AsyncState>
        </section>

        <aside className="adm__panel">
          <div className="adm__panel-head">
            <span className="label-mono">RBAC METRICS</span>
            <span className="material-symbols-outlined">shield</span>
          </div>
          <div className="adm__rbac">
            <div className="adm__rbac-metric"><span className="label-mono">ADMIN SEATS</span><strong>{q?.adminSeatsUsed ?? 0} / {q?.adminSeatsTotal ?? 0}</strong></div>
            <div className="adm__rbac-metric"><span className="label-mono">ENGINEER SEATS</span><strong>{q?.engineerSeatsUsed ?? 0} / {q?.engineerSeatsTotal ?? 0}</strong></div>
            <Button variant="secondary">Edit Policy Matrix</Button>
          </div>
        </aside>
      </div>

      <section className="adm__panel">
        <div className="adm__panel-head">
          <span className="label-mono">API CREDENTIALS</span>
          <button type="button" className="label-mono adm__more" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span className="material-symbols-outlined">add</span> CREATE KEY
          </button>
        </div>
        <div className="adm__creds-grid">
          {credentials.map((c) => (
            <div key={c.keyId} className="adm__cred-card">
              <div className="adm__cred-head">
                <span className="adm__cred-name">{c.name}</span>
                <span className="material-symbols-outlined">key</span>
              </div>
              <span className="label-mono adm__cred-created">CREATED: {c.createdAt}</span>
              <div className="adm__cred-key">
                <span>{c.maskedKey}</span>
                <button type="button" aria-label="Copy key"><span className="material-symbols-outlined">content_copy</span></button>
              </div>
              <div className="adm__cred-perms">
                {c.permissions.map((p) => <span key={p} className="adm__perm">{p}</span>)}
              </div>
              {c.lastUsedAt && <span className="label-mono adm__cred-used">LAST USED: {c.lastUsedAt}</span>}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
