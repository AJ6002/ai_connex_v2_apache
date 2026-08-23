import { Button, StatusBadge } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useJob, useResolveClarification } from '@/entities/job/hooks';
import type { Job, JobStage } from '@/entities/job/types';
import './JobView.css';

interface JobViewProps {
  jobId: string;
}

const STAGE_DOT: Record<JobStage['status'], string> = {
  DONE: 'job-stage__dot--done',
  RUNNING: 'job-stage__dot--running',
  FAILED: 'job-stage__dot--failed',
  PENDING: 'job-stage__dot--pending',
  SKIPPED: 'job-stage__dot--pending',
};

const STAGE_LABEL: Record<JobStage['status'], string> = {
  DONE: 'COMPLETED',
  RUNNING: 'RUNNING',
  FAILED: 'FAILED',
  PENDING: 'QUEUED',
  SKIPPED: 'SKIPPED',
};

export function JobView({ jobId }: JobViewProps) {
  const { data: job, isLoading, isError, error } = useJob(jobId);

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {job && <JobDetail job={job} routeJobId={jobId} />}
    </AsyncState>
  );
}

function JobDetail({ job, routeJobId }: { job: Job; routeJobId: string }) {
  // Resolve against the route's job id — the same key useJob cached under —
  // not job.jobId, which may be a different internal id from the fixture/backend.
  const resolve = useResolveClarification(routeJobId);
  const badgeStatus =
    job.status === 'COMPLETED'
      ? 'COMPLETED'
      : job.status === 'FAILED'
        ? 'FAILED'
        : job.status === 'AWAITING_CLARIFICATION'
          ? 'NEEDS_CLARIFICATION'
          : 'RUNNING';

  return (
    <div className="job">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="job__header">
        <div className="job__header-main">
          <div className="job__id-row">
            <span className="label-mono job__id">JOB ID: {job.jobId}</span>
            <StatusBadge status={badgeStatus} dot={job.status === 'RUNNING'} />
          </div>
          <h1 className="job__title">{job.title ?? 'Pipeline Execution'}</h1>
        </div>
        <div className="job__actions">
          <Button variant="secondary" size="sm">View Dataset</Button>
          <Button variant="secondary" size="sm">System Health</Button>
          {job.status === 'RUNNING' && (
            <button type="button" className="job__cancel label-mono">Cancel Job</button>
          )}
        </div>
      </header>

      {/* ── Stat cards ─────────────────────────────────────────────────── */}
      <div className="job__stats">
        <StatCard label="STARTED AT" value={job.startedAt ?? '—'} />
        <StatCard label="DURATION" value={job.durationLabel ?? '—'} icon="sync" />
        <StatCard label="INITIATED BY" value={job.initiatedBy ?? '—'} icon="person" />
        <StatCard label="DATASET REFERENCE" value={job.datasetRef ?? '—'} accent />
      </div>

      {/* ── Failure banner ─────────────────────────────────────────────── */}
      {job.status === 'FAILED' && job.failureReason && (
        <div className="job__failure">
          <span className="material-symbols-outlined">error</span>
          <div>
            <span className="label-mono">EXECUTION FAILED</span>
            <p>{job.failureReason}</p>
          </div>
          <Button variant="secondary" size="sm">Retry</Button>
        </div>
      )}

      {/* ── Clarification banner ───────────────────────────────────────── */}
      {job.status === 'AWAITING_CLARIFICATION' && job.clarification && (
        <div className="job__clarify">
          <span className="label-mono job__clarify-head">
            <span className="material-symbols-outlined">help</span> CLARIFICATION REQUIRED
          </span>
          <p>{job.clarification.question}</p>
          <div className="job__clarify-options">
            {job.clarification.options.map((opt) => (
              <button
                key={opt}
                type="button"
                className="job__clarify-opt label-mono"
                disabled={resolve.isPending}
                onClick={() => resolve.mutate(opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Pipeline + logs ────────────────────────────────────────────── */}
      <div className="job__grid">
        <section className="job__pipeline">
          <h2 className="label-mono job__section-title">EXECUTION PIPELINE</h2>
          <ol className="job__stages">
            {job.stages.map((stage, i) => (
              <li
                key={stage.key}
                className={`job-stage${stage.status === 'RUNNING' ? ' job-stage--active' : ''}${
                  i === job.stages.length - 1 ? ' job-stage--last' : ''
                }`}
              >
                <span className={`job-stage__dot ${STAGE_DOT[stage.status]}`} />
                <div className="job-stage__body">
                  <div className="job-stage__row">
                    <span className="job-stage__label">
                      {i + 1}. {stage.label}
                    </span>
                    <span className={`job-stage__status job-stage__status--${stage.status.toLowerCase()}`}>
                      {STAGE_LABEL[stage.status]}
                    </span>
                  </div>
                  {stage.status === 'RUNNING' && stage.detail && (
                    <>
                      <div className="job-stage__detail">
                        <span>{stage.detail}</span>
                        <span className="job-stage__pct">{stage.progressPct}%</span>
                      </div>
                      <div className="job-stage__bar">
                        <div style={{ width: `${stage.progressPct ?? 0}%` }} />
                      </div>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="job__right">
          <div className="job__logs">
            <div className="job__logs-head">
              <span className="label-mono">
                <span className="material-symbols-outlined">terminal</span> LIVE EXECUTION LOGS (FASTAPI)
              </span>
              {job.status === 'RUNNING' && (
                <span className="label-mono job__streaming">
                  <span className="job__streaming-dot" /> STREAMING
                </span>
              )}
            </div>
            <div className="job__console">
              {(job.logs ?? []).map((line, i) => (
                <div
                  key={i}
                  className={`job__log${line.includes('ERROR') ? ' job__log--error' : ''}${
                    line.includes('Active') ? ' job__log--active' : ''
                  }`}
                >
                  {line}
                </div>
              ))}
              {job.status === 'RUNNING' && <span className="job__cursor" />}
            </div>
          </div>

          {job.artifact && job.status === 'COMPLETED' ? (
            <div className="job__artifacts">
              <span className="material-symbols-outlined job__artifacts-icon">inventory_2</span>
              <div>
                <span className="job__artifacts-title">ARTIFACTS READY</span>
                <p>Model binary and evaluation report are available.</p>
              </div>
              <StatusBadge status="MACHINE_READY" />
            </div>
          ) : (
            <div className="job__artifacts job__artifacts--empty">
              <span className="material-symbols-outlined job__artifacts-icon">inventory_2</span>
              <div>
                <span className="job__artifacts-title">NO ARTIFACTS PRODUCED YET</span>
                <p>Model binaries and evaluation reports will appear here upon completion.</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string;
  icon?: string;
  accent?: boolean;
}) {
  return (
    <div className="job-stat">
      <span className="label-mono job-stat__label">{label}</span>
      <span className={`job-stat__value${accent ? ' job-stat__value--accent' : ''}`}>
        {icon && <span className="material-symbols-outlined">{icon}</span>}
        {value}
      </span>
    </div>
  );
}
