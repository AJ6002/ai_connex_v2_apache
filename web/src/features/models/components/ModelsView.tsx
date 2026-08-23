import { Link } from 'react-router-dom';
import { Button, EmptyState } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useModels } from '@/entities/model/hooks';
import type { ModelSpec } from '@/entities/model/types';
import './ModelsView.css';

const metric = (m: ModelSpec, name: string): string => {
  const found = m.metrics.find((x) => x.name === name);
  return found ? String(found.value) : '—';
};

const STATUS_CLASS: Record<string, string> = {
  READY: 'models-status--promoted',
  EVALUATING: 'models-status--evaluating',
  TRAINING: 'models-status--training',
  FAILED: 'models-status--failed',
  DEPRECATED: 'models-status--deprecated',
};
const STATUS_LABEL: Record<string, string> = { READY: 'PROMOTED' };

export function ModelsView() {
  const { data: models, isLoading, isError, error } = useModels();

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      <div className="models">
        <header className="models__header">
          <div>
            <h1 className="models__title">Model Registry</h1>
            <p className="label-mono models__sub">
              {models?.length ?? 0} ACTIVE ARTIFACTS // 5 PRODUCTION TARGETS
            </p>
          </div>
          <div className="models__actions">
            <Button variant="secondary">Compare Selected</Button>
            <Button variant="primary" rightIcon={<span className="material-symbols-outlined">north_east</span>}>
              Register New Model
            </Button>
          </div>
        </header>

        {!models || models.length === 0 ? (
          <EmptyState
            icon={<span className="material-symbols-outlined">deployed_code</span>}
            title="NO_MODELS_REGISTERED"
            description="Trained model artifacts will appear here once a training job completes and is promoted."
          />
        ) : (
          <div className="models__grid">
            <div className="models__table-wrap">
              <table className="models__table">
                <thead>
                  <tr>
                    <th className="models__check-col"><input type="checkbox" aria-label="Select all" /></th>
                    <th>MODEL ID</th>
                    <th>VERSION</th>
                    <th>STATUS</th>
                    <th>METRICS</th>
                    <th>TRAINING RUN</th>
                    <th>DEPLOYMENT</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m) => (
                    <tr key={m.modelId}>
                      <td><input type="checkbox" aria-label={`Select ${m.modelId}`} /></td>
                      <td className="models__id">
                        <Link to={`/models/${m.modelId}`}>{m.modelId}</Link>
                      </td>
                      <td className="models__mono">{m.version}</td>
                      <td>
                        <span className={`models-status ${STATUS_CLASS[m.status] ?? ''}`}>
                          {STATUS_LABEL[m.status] ?? m.status}
                        </span>
                      </td>
                      <td className="models__mono">
                        F1: <strong>{metric(m, 'f1')}</strong> // Acc: <strong>{metric(m, 'accuracy')}</strong>
                      </td>
                      <td><Link to="/jobs/job_completed" className="models__link">{m.trainingRun ?? '—'}</Link></td>
                      <td className="models__deploy">
                        {m.deployment && m.deployment !== '--' && <span className="models__deploy-dot" />}
                        {m.deployment ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <aside className="models__active">
              <span className="label-mono models__active-title">ACTIVE DATASET</span>
              <div className="models__active-thumb">
                <span className="material-symbols-outlined">dataset</span>
              </div>
              <span className="label-mono models__active-src">SOURCE</span>
              <span className="models__active-name">USER_BEHAVIOR_Q3</span>
            </aside>
          </div>
        )}
      </div>
    </AsyncState>
  );
}
