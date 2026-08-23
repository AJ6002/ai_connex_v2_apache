import { Link } from 'react-router-dom';
import { Button } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useRecentDatasets, useRecentJobs } from '@/entities/workspace/hooks';
import type { RecentJobSummary } from '@/entities/workspace/types';
import './WorkspaceOverviewView.css';

const JOB_STATUS_LABEL: Record<RecentJobSummary['status'], string> = {
  RUNNING: 'RUNNING',
  CLARIFICATION: 'CLARIFICATION',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  QUEUED: 'QUEUED',
};

/** Workspace Overview — faithful to STITCH-Design/ai_connex_workspace_overview. */
export function WorkspaceOverviewView() {
  const { data: jobs = [], isLoading, isError, error } = useRecentJobs();
  const { data: datasets = [] } = useRecentDatasets();

  const clarificationCount = jobs.filter((j) => j.status === 'CLARIFICATION').length;

  return (
    <div className="wov">
      {/* ── Top row: quick actions / throughput / active deployment ────── */}
      <div className="wov__top">
        <section className="wov__panel">
          <div className="wov__panel-head"><span className="label-mono">QUICK ACTIONS</span></div>
          <div className="wov__actions">
            <Link to="/intake" className="wov__action">Intake New Data</Link>
            <Link to="/data-studio" className="wov__action">Launch Experiment</Link>
            <Link to="/deployments/new" className="wov__action">Deploy Model</Link>
            <Link to="/data-studio" className="wov__action">Open Data Studio</Link>
          </div>
        </section>

        <section className="wov__panel">
          <div className="wov__panel-head">
            <span className="label-mono">INFERENCE THROUGHPUT</span>
            <span className="material-symbols-outlined">trending_up</span>
          </div>
          <span className="wov__stat-value">1.2k<span className="wov__stat-unit">req/s</span></span>
          <span className="wov__stat-sub">SLA 99.4%</span>
        </section>

        <section className="wov__panel">
          <div className="wov__panel-head">
            <span className="label-mono">ACTIVE DEPLOYMENT</span>
            <span className="material-symbols-outlined">check_circle</span>
          </div>
          <span className="wov__stat-value">v2.4.1</span>
          <span className="wov__stat-sub">8.4min turnaround</span>
        </section>
      </div>

      {/* ── Attention banner ─────────────────────────────────────────────── */}
      {clarificationCount > 0 && (
        <div className="wov__alert">
          <span className="material-symbols-outlined">warning</span>
          <span className="wov__alert-text">
            ITEMS REQUIRING ATTENTION: {clarificationCount} job{clarificationCount > 1 ? 's' : ''} require
            clarification or user correction. High priority.
          </span>
          <Button variant="secondary" size="sm">Review Jobs</Button>
        </div>
      )}

      <div className="wov__grid">
        {/* ── Active & recent jobs ───────────────────────────────────────── */}
        <section className="wov__panel">
          <div className="wov__panel-head">
            <span className="label-mono">ACTIVE &amp; RECENT JOBS</span>
            <Link to="/jobs/job_running" className="label-mono" style={{ color: 'var(--color-assistant-identity)', textDecoration: 'none' }}>
              VIEW ALL
            </Link>
          </div>
          <AsyncState isLoading={isLoading} isError={isError} error={error}>
            <table className="wov__jobs-table">
              <thead><tr><th>JOB ID</th><th>TYPE</th><th>STATUS</th><th>PROGRESS</th><th>START TIME</th></tr></thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.jobId} className={j.status === 'CLARIFICATION' ? 'wov__row--clarify' : undefined}>
                    <td className="wov__job-id">
                      <Link to={`/jobs/${j.jobId.includes('8293') ? 'job_clarify' : j.jobId.includes('8290') ? 'job_completed' : 'job_running'}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                        {j.jobId}
                      </Link>
                    </td>
                    <td>{j.jobType}</td>
                    <td>
                      <span className={`wov__job-status wov__job-status--${j.status.toLowerCase()}`}>
                        <span className="wov__job-status-dot" /> {JOB_STATUS_LABEL[j.status]}
                      </span>
                    </td>
                    <td>
                      <div className={`wov__progress wov__progress--${j.status.toLowerCase()}`}>
                        <div style={{ width: `${j.progressPct}%` }} />
                      </div>
                    </td>
                    <td>{j.startTime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </AsyncState>
        </section>

        {/* ── Recent datasets ─────────────────────────────────────────────── */}
        <aside className="wov__panel">
          <div className="wov__panel-head">
            <span className="label-mono">RECENT DATASETS</span>
            <span className="material-symbols-outlined">more_horiz</span>
          </div>
          <div className="wov__datasets">
            {datasets.map((d) => (
              <div key={d.datasetRef} className={`wov__dataset-card${d.status === 'FAILED' ? ' wov__dataset-card--failed' : ''}`}>
                <div className="wov__dataset-row">
                  <span className="wov__dataset-name">{d.name}</span>
                  <span className={`wov__dataset-chip wov__dataset-chip--${d.status.toLowerCase()}`}>{d.status}</span>
                </div>
                <div className="wov__dataset-meta">
                  <span>{d.sizeLabel}</span>
                  <span className="label-mono">{d.updatedLabel}</span>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
