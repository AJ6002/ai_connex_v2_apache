import { Button } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useModelDetail } from '@/entities/model/hooks';
import type { ModelSpec } from '@/entities/model/types';
import './ModelDetailView.css';

interface Props {
  modelId: string;
}

const metric = (m: ModelSpec, name: string) => m.metrics.find((x) => x.name === name);

export function ModelDetailView({ modelId }: Props) {
  const { data: model, isLoading, isError, error } = useModelDetail(modelId);

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {model && (
        <div className="mdl">
          {/* ── Header ───────────────────────────────────────────────────── */}
          <header className="mdl__header">
            <div className="mdl__header-main">
              <div className="mdl__badges label-mono">
                <span className="mdl__ver">{model.version}</span>
                <span className="mdl__ready">MACHINE_READY</span>
              </div>
              <h1 className="mdl__title">{model.modelId}</h1>
              <p className="mdl__origin">
                Origin: {model.trainingRun ?? '—'} • Created: {new Date(model.createdAt).toUTCString()}
              </p>
            </div>
            <div className="mdl__actions">
              <Button variant="secondary" leftIcon={<span className="material-symbols-outlined">close</span>}>
                Reject Version
              </Button>
              <Button variant="primary" rightIcon={<span className="material-symbols-outlined">cloud_upload</span>}>
                Approve for Production
              </Button>
            </div>
          </header>

          <div className="mdl__grid">
            {/* Evaluation metrics */}
            <section className="mdl__panel mdl__metrics">
              <span className="label-mono mdl__panel-title">EVALUATION METRICS</span>
              <div className="mdl__metric-row">
                <Metric label="F1-SCORE" value={String(metric(model, 'f1')?.value ?? '—')} delta="+0.012 vs V1.2.3" tone="up" />
                <Metric
                  label="LATENCY (P99)"
                  value={`${metric(model, 'latency_p99')?.value ?? '—'}ms`}
                  delta="+3ms vs V1.2.3"
                  tone="down"
                />
                <Metric label="AUC-ROC" value={String(metric(model, 'auc_roc')?.value ?? '—')} delta="Stable" tone="flat" />
              </div>
              <div className="mdl__chart">
                <span className="label-mono mdl__chart-label">Precision / Recall Curve</span>
                <svg viewBox="0 0 400 160" preserveAspectRatio="none" className="mdl__curve">
                  <path d="M0,155 C120,150 240,60 400,20" fill="none" stroke="var(--color-outline-variant)" strokeWidth="3" />
                </svg>
              </div>
            </section>

            {/* Validation */}
            <section className="mdl__panel">
              <span className="label-mono mdl__panel-title">VALIDATION RESULTS</span>
              <div className="mdl__validation">
                <div className="mdl__val-row">
                  <span className="material-symbols-outlined mdl__val-ok">check_circle</span>
                  <div>
                    <span className="label-mono mdl__val-name">COMPLIANCE CHECK</span>
                    <p>PASSED</p>
                  </div>
                </div>
                <div className="mdl__val-row">
                  <span className="material-symbols-outlined mdl__val-ok">verified_user</span>
                  <div>
                    <span className="label-mono mdl__val-name">BIAS AUDIT</span>
                    <p>WITHIN TOLERANCE</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Lineage */}
            <section className="mdl__panel">
              <span className="label-mono mdl__panel-title">ARTIFACT LINEAGE</span>
              <ol className="mdl__lineage">
                <LineageNode name="DS-USER-EVENTS-Q3" kind="Dataset" />
                <LineageNode name="FS-ENGAGEMENT-V2" kind="Feature Set" />
                <LineageNode name={`${model.modelId}-${model.version}`} kind="Model Artifact" active last />
              </ol>
            </section>

            {/* References + deployment history */}
            <div className="mdl__col">
              <section className="mdl__panel">
                <span className="label-mono mdl__panel-title">ARTIFACT REFERENCES</span>
                <div className="mdl__refs">
                  <RefRow icon="description" name="model_weights.bin" />
                  <RefRow icon="data_object" name="config.yaml" />
                </div>
              </section>

              <section className="mdl__panel">
                <div className="mdl__panel-head">
                  <span className="label-mono mdl__panel-title">DEPLOYMENT HISTORY</span>
                  <a href="#deploy" className="label-mono mdl__deploy-edge">DEPLOY TO EDGE</a>
                </div>
                <table className="mdl__deploy-table">
                  <thead><tr><th>TARGET</th><th>STATUS</th></tr></thead>
                  <tbody>
                    <tr><td>EDGE-NODE-12</td><td><span className="mdl__dot mdl__dot--run" /> RUNNING</td></tr>
                    <tr><td>STAGING-CLUSTER</td><td><span className="mdl__dot" /> STOPPED</td></tr>
                  </tbody>
                </table>
              </section>
            </div>
          </div>
        </div>
      )}
    </AsyncState>
  );
}

function Metric({ label, value, delta, tone }: { label: string; value: string; delta: string; tone: 'up' | 'down' | 'flat' }) {
  return (
    <div className="mdl__metric">
      <span className="label-mono mdl__metric-label">{label}</span>
      <strong className="mdl__metric-value">{value}</strong>
      <span className={`mdl__metric-delta mdl__metric-delta--${tone}`}>{delta}</span>
    </div>
  );
}

function LineageNode({ name, kind, active, last }: { name: string; kind: string; active?: boolean; last?: boolean }) {
  return (
    <li className={`mdl__lin${last ? ' mdl__lin--last' : ''}`}>
      <span className="mdl__lin-dot" />
      <div className={`mdl__lin-card${active ? ' mdl__lin-card--active' : ''}`}>
        <span className="mdl__lin-name">{name}</span>
        <span className="mdl__lin-kind">{kind}</span>
      </div>
    </li>
  );
}

function RefRow({ icon, name }: { icon: string; name: string }) {
  return (
    <div className="mdl__ref">
      <span className="mdl__ref-left">
        <span className="material-symbols-outlined">{icon}</span>
        <span className="mdl__ref-name">{name}</span>
      </span>
      <button type="button" className="mdl__ref-dl" aria-label={`Download ${name}`}>
        <span className="material-symbols-outlined">download</span>
      </button>
    </div>
  );
}
