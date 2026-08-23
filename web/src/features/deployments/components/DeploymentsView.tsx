import { Link } from 'react-router-dom';
import { Button, EmptyState } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useDeployments } from '@/entities/deployment/hooks';
import './DeploymentsView.css';

const STATUS_CLASS: Record<string, string> = {
  ACTIVE: 'dep-status--active',
  DEGRADED: 'dep-status--degraded',
  STOPPED: 'dep-status--stopped',
  FAILED: 'dep-status--failed',
  PENDING: 'dep-status--pending',
};

export function DeploymentsView() {
  const { data: deployments, isLoading, isError, error } = useDeployments();

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      <div className="deps">
        <header className="deps__header">
          <div>
            <h1 className="deps__title">Deployments</h1>
            <p className="label-mono deps__sub">{deployments?.length ?? 0} SERVING TARGETS // LIVE INFERENCE</p>
          </div>
          <Button variant="primary" href="/deployments/new" rightIcon={<span className="material-symbols-outlined">north_east</span>}>
            Deploy New
          </Button>
        </header>

        {!deployments || deployments.length === 0 ? (
          <EmptyState icon={<span className="material-symbols-outlined">rocket_launch</span>} title="NO_ACTIVE_DEPLOYMENTS" description="Promoted models deployed to serving infrastructure will appear here." />
        ) : (
          <div className="deps__list">
            {deployments.map((d) => (
              <Link to={`/deployments/${d.deploymentId}`} key={d.deploymentId} className="deps__card">
                <div className="deps__card-head">
                  <span className={`dep-status ${STATUS_CLASS[d.status] ?? ''}`}>
                    <span className="dep-status__dot" /> {d.status}
                  </span>
                  <span className="label-mono deps__env">{d.environment}</span>
                </div>
                <h2 className="deps__card-id">{d.deploymentId}</h2>
                <p className="deps__card-model label-mono">{d.modelRef}</p>
                <div className="deps__card-metrics">
                  <div><span className="label-mono">LATENCY</span><strong>{d.metrics.avgLatencyMs}ms</strong></div>
                  <div><span className="label-mono">THROUGHPUT</span><strong>{d.metrics.requestsPerSecond}/s</strong></div>
                  <div><span className="label-mono">REPLICAS</span><strong>{d.replicas}</strong></div>
                </div>
                <code className="deps__card-endpoint">{d.endpointUrl}</code>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AsyncState>
  );
}
