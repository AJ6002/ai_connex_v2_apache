import { Button } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useAuditLogs } from '@/entities/workspace/hooks';
import './AuditLogsView.css';

/** Audit Logs — faithful to STITCH-Design/ai_connex_admin_audit_logs. */
export function AuditLogsView() {
  const { data: logs = [], isLoading, isError, error } = useAuditLogs();

  return (
    <div className="audit">
      <span className="audit__crumb">SETTINGS &gt; <strong>AUDIT LOGS</strong></span>

      <header className="audit__header">
        <div>
          <h1 className="audit__title">Platform Activity</h1>
          <p className="audit__sub">
            Chronological, immutable record of all administrative and system-level events across
            the workspace environment.
          </p>
        </div>
        <div className="audit__header-actions">
          <Button variant="secondary" leftIcon={<span className="material-symbols-outlined">tune</span>}>Advanced Filters</Button>
          <Button variant="primary" leftIcon={<span className="material-symbols-outlined">download</span>}>Export Audit Data</Button>
        </div>
      </header>

      <div className="audit__filters">
        <label className="audit__field">
          <span className="label-mono">SEARCH EVENTS</span>
          <div className="audit__search">
            <span className="material-symbols-outlined">search</span>
            <input placeholder="ID, User, or Entity..." aria-label="Search events" />
          </div>
        </label>
        <label className="audit__field">
          <span className="label-mono">EVENT TYPE</span>
          <div className="audit__select">
            <select defaultValue="all">
              <option value="all">All Types</option>
              <option>Policy Update</option>
              <option>Deployment</option>
              <option>Access Denied</option>
            </select>
            <span className="material-symbols-outlined">expand_more</span>
          </div>
        </label>
        <label className="audit__field">
          <span className="label-mono">DATE RANGE</span>
          <div className="audit__select">
            <select defaultValue="24h">
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <span className="material-symbols-outlined">expand_more</span>
          </div>
        </label>
      </div>

      <AsyncState isLoading={isLoading} isError={isError} error={error}>
        <div className="audit__table-wrap">
          <table className="audit__table">
            <thead>
              <tr><th>TIMESTAMP (UTC)</th><th>USER / PRINCIPAL</th><th>ACTION</th><th>ENTITY ID</th><th>STATUS</th></tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.entryId} className={log.status === 'FAILURE' ? 'audit__row--failure' : undefined}>
                  <td className="audit__ts">{log.timestampUtc}</td>
                  <td>
                    <span className="audit__principal">
                      <span className="material-symbols-outlined">
                        {log.principalType === 'service' ? 'settings_suggest' : 'person'}
                      </span>
                      {log.principal}
                    </span>
                  </td>
                  <td><span className="audit__action">{log.action}</span></td>
                  <td className="audit__entity">{log.entityId}</td>
                  <td>
                    <span className={`audit__status audit__status--${log.status.toLowerCase()}`}>
                      <span className="audit__status-dot" /> {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="audit__footer">
            <span>Showing 1-{logs.length} of 12,049 events</span>
            <div className="audit__pager">
              <button type="button" aria-label="Previous page"><span className="material-symbols-outlined">chevron_left</span></button>
              <button type="button" aria-label="Next page"><span className="material-symbols-outlined">chevron_right</span></button>
            </div>
          </div>
        </div>
      </AsyncState>
    </div>
  );
}
