import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';
import { useSubmitIntent } from '@/entities/job/hooks';
import { useInspectArchive } from '@/entities/dataset/hooks';
import './IntakeView.css';

type Sensitivity = 'PUBLIC' | 'INTERNAL' | 'RESTRICTED';

const RECENT = [
  { file: 'dataset_q3_rev.csv', status: 'Scanning schemas... 45%', tone: 'amber' as const },
  { file: 'user_metrics_v2.json', status: 'Initializing pipeline...', tone: 'cyan' as const },
];

export function IntakeView() {
  const navigate = useNavigate();
  const submitIntent = useSubmitIntent();
  const inspectArchive = useInspectArchive();

  const [source, setSource] = useState('Internal Telemetry');
  const [sensitivity, setSensitivity] = useState<Sensitivity>('INTERNAL');
  const [ownerId, setOwnerId] = useState('USR-9942-A');

  const busy = inspectArchive.isPending || submitIntent.isPending;

  const handleBrowse = () => {
    const uri = 's3://internal-telemetry/dataset_q3.csv';
    inspectArchive.mutate(uri, {
      onSuccess: () => {
        submitIntent.mutate(
          {
            goal: 'Register and profile incoming telemetry asset',
            requestedOutputs: ['profile'],
            sourceRefs: [uri],
          },
          { onSuccess: (job) => navigate(`/jobs/${job.jobId}`) },
        );
      },
    });
  };

  return (
    <div className="intake">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="intake__header">
        <div>
          <h1 className="intake__title">Asset Registration</h1>
          <p className="intake__subtitle">
            Initialize and classify incoming data schemas for model training.
          </p>
        </div>
        <Button variant="secondary" leftIcon={<span className="material-symbols-outlined">add</span>}>
          Batch Import
        </Button>
      </header>

      {/* ── Grid ───────────────────────────────────────────────────────── */}
      <div className="intake__grid">
        {/* Drop zone */}
        <section className="panel intake__dropzone-panel">
          <div className="panel__head">
            <span className="label-mono">DROP_ZONE_ALPHA</span>
            <span className="material-symbols-outlined panel__head-icon">cloud_upload</span>
          </div>
          <div className="intake__dropzone">
            <span className="material-symbols-outlined intake__dropzone-icon">download</span>
            <p className="intake__dropzone-title">Drag &amp; Drop Assets</p>
            <p className="intake__dropzone-hint">
              Supports CSV, JSON, Parquet, and proprietary schema definitions up to 50GB.
            </p>
            <Button variant="primary" onClick={handleBrowse} loading={busy}>
              Browse Local Files
            </Button>
          </div>
        </section>

        {/* Right column */}
        <div className="intake__side">
          <section className="panel">
            <div className="panel__head">
              <span className="label-mono intake__accent-lime">METADATA_CONFIG</span>
            </div>
            <div className="panel__body intake__meta">
              <label className="intake__field">
                <span className="label-mono">SOURCE_ORIGIN</span>
                <div className="intake__select">
                  <select value={source} onChange={(e) => setSource(e.target.value)}>
                    <option>Internal Telemetry</option>
                    <option>External Upload</option>
                    <option>Streaming Connector</option>
                  </select>
                  <span className="material-symbols-outlined">expand_more</span>
                </div>
              </label>

              <div className="intake__field">
                <span className="label-mono">SENSITIVITY_LEVEL</span>
                <div className="intake__segmented" role="group">
                  {(['PUBLIC', 'INTERNAL', 'RESTRICTED'] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      className={`intake__seg label-mono${sensitivity === s ? ' intake__seg--active' : ''}`}
                      onClick={() => setSensitivity(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <label className="intake__field">
                <span className="label-mono">DATA_OWNER_ID</span>
                <div className="intake__input">
                  <span className="material-symbols-outlined">badge</span>
                  <input value={ownerId} onChange={(e) => setOwnerId(e.target.value)} />
                </div>
              </label>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <span className="label-mono">RECENT_INTAKE</span>
              <span className="label-mono intake__accent-lime">LIVE</span>
            </div>
            <div className="panel__body intake__recent">
              {RECENT.map((r) => (
                <div key={r.file} className={`intake__recent-row intake__recent-row--${r.tone}`}>
                  <span className="intake__recent-file">{r.file}</span>
                  <span className={`intake__recent-status intake__accent-${r.tone}`}>{r.status}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
