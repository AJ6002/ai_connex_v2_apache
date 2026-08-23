import { Button, StatusBadge } from '@/components/ui';
import { Link } from 'react-router-dom';
import { AsyncState } from '@/components/AsyncState';
import { useProfileSummary } from '@/entities/profile/hooks';
import './DataStudioView.css';

const STAGES = [
  { key: 'DISCOVERY', label: 'Discovery', state: 'done' },
  { key: 'PROFILE', label: 'Profile', state: 'active' },
  { key: 'PREPARE', label: 'Prepare', state: 'locked' },
  { key: 'FEATURES', label: 'Features', state: 'locked' },
  { key: 'TRAIN', label: 'Train', state: 'locked' },
  { key: 'EVALUATE', label: 'Evaluate', state: 'locked' },
] as const;

const HIST = [8, 18, 34, 62, 100, 74, 30, 14, 6];
const TEMPORAL = [40, 46, 52, 48, 30, 58, 64, 70, 62, 76];

const TYPE_ICON: Record<string, string> = {
  datetime: 'calendar_month',
  float: 'tag',
  int: 'key',
  string: 'account_tree',
};

export function DataStudioView() {
  const { data: profile, isLoading, isError, error } = useProfileSummary('ds-001');

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {profile && (
        <div className="ds">
          {/* ── Breadcrumb stage stepper ─────────────────────────────────── */}
          <nav className="ds__stages" aria-label="Pipeline stage">
            {STAGES.map((s, i) => {
              const icon = s.state === 'done' ? 'check_circle' : s.state === 'active' ? 'radio_button_checked' : 'lock';
              const content = (
                <>
                  <span className="material-symbols-outlined">{icon}</span>
                  {s.label}
                </>
              );
              return (
                <span key={s.key} className={`ds__stage ds__stage--${s.state}`}>
                  {s.key === 'DISCOVERY' ? (
                    <Link to="/data-studio/discovery/asset_demo_0001" className="ds__stage-link">{content}</Link>
                  ) : (
                    content
                  )}
                  {i < STAGES.length - 1 && <span className="ds__stage-sep material-symbols-outlined">chevron_right</span>}
                </span>
              );
            })}
          </nav>

          {/* ── Header ───────────────────────────────────────────────────── */}
          <header className="ds__header">
            <div>
              <h1 className="ds__title">{profile.datasetName ?? 'Q3_Financial_Export_v2.csv'}</h1>
              <div className="ds__meta label-mono">
                <span><span className="material-symbols-outlined">cloud</span> AWS S3 // BUCKET-FIN-PROD-03</span>
                <span><span className="material-symbols-outlined">schedule</span> LAST SYNC: 2 HOURS AGO</span>
                <span><span className="material-symbols-outlined">database</span> 4.2 GB</span>
              </div>
            </div>
            <Button variant="primary" rightIcon={<span className="material-symbols-outlined">north_east</span>}>
              Proceed to Preparation
            </Button>
          </header>

          <div className="ds__grid">
            {/* ── Resolved tables ────────────────────────────────────────── */}
            <aside className="ds__tables">
              <span className="label-mono ds__tables-title">RESOLVED TABLES</span>
              <button type="button" className="ds__table ds__table--active">
                <div className="ds__table-row">
                  <span className="ds__table-name">{profile.datasetName ?? 'transactions_main'}</span>
                  <span className="material-symbols-outlined ds__table-check">check_circle</span>
                </div>
                <StatusBadge status="MACHINE_READY" size="sm" />
              </button>
              <button type="button" className="ds__table">
                <div className="ds__table-row">
                  <span className="ds__table-name">user_metadata</span>
                  <span className="material-symbols-outlined">hourglass_empty</span>
                </div>
                <StatusBadge status="READY_FOR_PROFILER" size="sm" />
              </button>
            </aside>

            {/* ── Profiling panels ───────────────────────────────────────── */}
            <div className="ds__main">
              {/* Score banner */}
              <div className="ds__score">
                <div className="ds__score-ring">98.2</div>
                <div className="ds__score-text">
                  <h2>Machine Ready</h2>
                  <p>Data Integrity Score indicates high confidence for feature engineering phase.</p>
                </div>
                <div className="ds__score-metric">
                  <span className="label-mono">ROWS</span>
                  <strong>{profile.rowCount?.toLocaleString() ?? '14,204,911'}</strong>
                </div>
                <div className="ds__score-metric">
                  <span className="label-mono">COLUMNS</span>
                  <strong>{profile.columnCount ?? 42}</strong>
                </div>
              </div>

              <div className="ds__panels">
                {/* 1. Structural */}
                <section className="ds__panel">
                  <div className="ds__panel-head">
                    <span className="label-mono">1. STRUCTURAL PROFILE</span>
                    <span className="label-mono ds__panel-meta">MEMORY: ~1.2GB</span>
                  </div>
                  <table className="ds__fields">
                    <thead>
                      <tr><th>FIELD NAME</th><th>TYPE</th><th>NULLS</th></tr>
                    </thead>
                    <tbody>
                      {profile.columns.map((c) => (
                        <tr key={c.name}>
                          <td>
                            <span className="material-symbols-outlined">
                              {TYPE_ICON[c.dtype] ?? 'data_object'}
                            </span>
                            {c.name}
                          </td>
                          <td><span className="ds__type">{c.dtype}</span></td>
                          <td>{(c.nullRatio * 100).toFixed(c.nullRatio < 0.01 ? 3 : 1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>

                {/* 4. Semantic */}
                <section className="ds__panel">
                  <div className="ds__panel-head"><span className="label-mono">4. SEMANTIC PROFILE</span></div>
                  <div className="ds__semantic">
                    <SemanticRow icon="badge" label="PII Detected" chip="ACCOUNT IDS" tone="pink" />
                    <SemanticRow icon="payments" label="Currency Entity" chip="USD (99.8%)" tone="muted" />
                    <SemanticRow icon="sell" label="Taxonomy Map" chip="CATEGORY LABELS" tone="muted" />
                  </div>
                </section>

                {/* 2. Statistical */}
                <section className="ds__panel">
                  <div className="ds__panel-head">
                    <span className="label-mono">2. STATISTICAL PROFILE</span>
                    <span className="label-mono ds__panel-meta">AMOUNT_USD DISTRIBUTION</span>
                  </div>
                  <div className="ds__chart">
                    {HIST.map((h, i) => (
                      <span key={i} className={`ds__bar${i === 4 ? ' ds__bar--peak' : i === 3 ? ' ds__bar--hi' : ''}`} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className="ds__stats-row">
                    <div><span className="label-mono">MEAN</span><strong>$124.50</strong></div>
                    <div><span className="label-mono">MEDIAN</span><strong>$45.00</strong></div>
                    <div><span className="label-mono">STD DEV</span><strong>$890.12</strong></div>
                  </div>
                </section>

                {/* 3. Temporal */}
                <section className="ds__panel">
                  <div className="ds__panel-head">
                    <span className="label-mono">3. TEMPORAL PROFILE</span>
                    <span className="label-mono ds__panel-meta">Q3 DENSITY</span>
                  </div>
                  <div className="ds__chart ds__chart--temporal">
                    {TEMPORAL.map((h, i) => (
                      <span key={i} className={`ds__bar${i === 4 ? ' ds__bar--anomaly' : ''}`} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <div className="ds__axis label-mono"><span>JUL 1</span><span>AUG 15</span><span>SEP 30</span></div>
                </section>
              </div>
            </div>
          </div>
        </div>
      )}
    </AsyncState>
  );
}

function SemanticRow({ icon, label, chip, tone }: { icon: string; label: string; chip: string; tone: 'pink' | 'muted' }) {
  return (
    <div className="ds__sem-row">
      <span className="ds__sem-left">
        <span className="material-symbols-outlined">{icon}</span>
        {label}
      </span>
      <span className={`ds__sem-chip ds__sem-chip--${tone} label-mono`}>{chip}</span>
    </div>
  );
}
