import { Button, StatusBadge } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useDeploymentDetail } from '@/entities/deployment/hooks';
import './DeploymentDetailView.css';

interface Props {
  deploymentId: string;
}

const HISTORY = [
  { version: 'v1.2.4 (Current)', at: '2023-10-27 14:32 UTC', status: 'Active', by: 'CI/CD Pipeline', canRollback: false },
  { version: 'v1.2.3', at: '2023-10-20 09:15 UTC', status: 'Inactive', by: 'Manual (jdoe)', canRollback: true },
  { version: 'v1.2.2', at: '2023-10-15 11:00 UTC', status: 'Failed', by: 'CI/CD Pipeline', canRollback: false },
];

export function DeploymentDetailView({ deploymentId }: Props) {
  const { data: dep, isLoading, isError, error } = useDeploymentDetail(deploymentId);

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {dep && (
        <div className="depd">
          {/* Header */}
          <header className="depd__header">
            <div>
              <div className="depd__badge-row">
                <StatusBadge status={dep.status === 'ACTIVE' ? 'RUNNING' : 'FAILED'} dot />
                <span className="depd__env">{dep.environment === 'PRODUCTION' ? 'Production Environment' : dep.environment}</span>
              </div>
              <h1 className="depd__title">
                {dep.deploymentId}
                <button type="button" className="depd__copy" aria-label="Copy id">
                  <span className="material-symbols-outlined">content_copy</span>
                </button>
              </h1>
            </div>
            <div className="depd__actions">
              <Button variant="secondary" leftIcon={<span className="material-symbols-outlined">pause</span>}>Suspend</Button>
              <Button variant="primary" leftIcon={<span className="material-symbols-outlined">autorenew</span>}>Update Version</Button>
            </div>
          </header>

          <div className="depd__grid">
            {/* Identity & config */}
            <section className="depd__panel">
              <div className="depd__panel-head">
                <span className="label-mono">IDENTITY &amp; CONFIG</span>
                <span className="material-symbols-outlined depd__panel-icon">data_object</span>
              </div>
              <div className="depd__field">
                <span className="label-mono">MODEL VERSION</span>
                <strong>{dep.modelRef}</strong>
              </div>
              <div className="depd__field">
                <span className="label-mono">SERVING ENDPOINT URL</span>
                <div className="depd__endpoint">
                  <span>{dep.endpointUrl}</span>
                  <button type="button" aria-label="Copy endpoint"><span className="material-symbols-outlined">content_copy</span></button>
                </div>
              </div>
              <div className="depd__field-row">
                <div className="depd__field">
                  <span className="label-mono">COMPUTE REGION</span>
                  <strong>{dep.computeRegion ?? '—'}</strong>
                </div>
                <div className="depd__field">
                  <span className="label-mono">INSTANCE TYPE</span>
                  <strong>{dep.instanceType ?? '—'}</strong>
                </div>
              </div>
            </section>

            {/* Health & performance */}
            <section className="depd__panel">
              <span className="label-mono depd__panel-head">HEALTH &amp; PERFORMANCE (LAST 24H)</span>
              <div className="depd__health">
                <div className="depd__health-metric"><span className="label-mono">AVG LATENCY (P99)</span><strong>{dep.metrics.avgLatencyMs} ms</strong></div>
                <div className="depd__health-metric"><span className="label-mono">THROUGHPUT</span><strong>{(dep.metrics.requestsPerSecond / 1000).toFixed(1)}k req/s</strong></div>
                <div className="depd__health-metric"><span className="label-mono">ERROR RATE</span><strong>{dep.errorRatePct ?? 0} %</strong></div>
              </div>
              <div className="depd__chart">
                <svg viewBox="0 0 500 200" preserveAspectRatio="none" className="depd__spark">
                  <polyline
                    points="0,170 60,150 110,160 160,120 210,140 280,95 340,105 400,70 450,55 500,65"
                    fill="none"
                    stroke="var(--color-status-running)"
                    strokeWidth="3"
                  />
                </svg>
              </div>
            </section>
          </div>

          {/* Version history */}
          <section className="depd__panel">
            <span className="label-mono depd__panel-head">VERSION HISTORY</span>
            <table className="depd__history">
              <thead><tr><th>VERSION</th><th>DEPLOYED AT</th><th>STATUS</th><th>TRIGGERED BY</th><th>ACTION</th></tr></thead>
              <tbody>
                {HISTORY.map((h) => (
                  <tr key={h.version}>
                    <td className="depd__mono">{h.version}</td>
                    <td className="depd__mono">{h.at}</td>
                    <td>
                      <span className={`depd__hstatus depd__hstatus--${h.status.toLowerCase()}`}>
                        <span className="material-symbols-outlined">
                          {h.status === 'Active' ? 'check_circle' : h.status === 'Failed' ? 'error' : 'history'}
                        </span>
                        {h.status}
                      </span>
                    </td>
                    <td>{h.by}</td>
                    <td className="depd__action">
                      {h.canRollback ? <a href="#rollback">Rollback</a> : <span className="depd__action--off">Rollback</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      )}
    </AsyncState>
  );
}
