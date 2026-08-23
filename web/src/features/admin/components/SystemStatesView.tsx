import { EmptyState } from '@/components/ui';
import './SystemStatesView.css';

/**
 * System States & Errors — a diagnostic gallery of every state the app can
 * render, faithful to STITCH-Design's application_states_operational and
 * application_states_failure_progress screens. Reachable from Admin as a
 * reference/QA tool, not a route users hit organically.
 */
export function SystemStatesView() {
  return (
    <div className="states">
      <header className="states__header">
        <h1 className="states__title">System States &amp; Errors</h1>
        <p className="label-mono states__version">DIAGNOSTIC_OVERVIEW_V2.4</p>
      </header>

      <div className="states__grid">
        {/* Validation failure */}
        <section className="states__card states__card--failure">
          <div className="states__card-head">
            <span className="states__card-label">
              <span className="material-symbols-outlined">warning</span> VALIDATION FAILURE
            </span>
            <span className="states__card-code">ERR_SCHEMA_MISMATCH</span>
          </div>
          <p className="states__body">
            Data corruption detected during ingestion phase. Schema validation failed for dataset
            <code> customer_metrics_q3</code>.
          </p>
          <div className="states__log">
            &gt; VALIDATION_LOG:
            <br />
            Line 4092: Expected type INT64 for column &apos;revenue&apos;, got STRING (&quot;N/A&quot;).
            <br />
            Line 5110: Null value found in non-nullable column &apos;user_id&apos;.
            <br /><br />
            &gt; <span className="states__log-action">ACTION_REQUIRED: FIX_DATA_OR_UPDATE_SCHEMA</span>
          </div>
          <div className="states__actions">
            <button type="button" className="states__btn">VIEW_FULL_LOG</button>
            <button type="button" className="states__btn states__btn--danger">ABORT_JOB</button>
          </div>
        </section>

        {/* Asset quarantined */}
        <section className="states__card states__card--warning">
          <div className="states__card-head">
            <span className="states__card-label">
              <span className="material-symbols-outlined">shield</span> ASSET QUARANTINED
            </span>
            <span className="states__card-code">SEC_LOCKDOWN_0x9A</span>
          </div>
          <p className="states__body">
            This asset has been automatically quarantined due to policy violations. Access is
            restricted to compliance administrators.
          </p>
          <div className="states__reason">
            <span className="states__reason-head">
              <span className="material-symbols-outlined">shield</span> REASON: PII_DETECTED
            </span>
            <p>
              Unmasked Social Security Numbers detected in Column A (<code>ssn_raw</code>). Asset
              blocked pending review or masking pipeline execution.
            </p>
          </div>
          <div className="states__actions">
            <button type="button" className="states__btn">REQUEST_REVIEW</button>
            <button type="button" className="states__btn states__btn--warning">TRIGGER_MASKING</button>
          </div>
        </section>

        {/* 403 Forbidden */}
        <section className="states__card states__card--neutral">
          <span className="material-symbols-outlined states__icon-xl">block</span>
          <span className="states__code-xl">403 Forbidden</span>
          <p className="states__desc">
            You do not have the required IAM roles (<code>mlops.models.deploy</code>) to perform
            this action on the current resource cluster.
          </p>
          <div className="states__actions">
            <button type="button" className="states__btn">BACK_TO_SAFETY</button>
            <button type="button" className="states__btn states__btn--primary">ESCALATION_PROTOCOL</button>
          </div>
        </section>

        {/* 503 Service Unavailable */}
        <section className="states__card states__card--info">
          <div className="states__card-head">
            <span className="states__card-label" style={{ color: 'var(--color-on-surface-variant)' }}>
              <span className="material-symbols-outlined">cloud_off</span> SERVICE UNAVAILABLE
            </span>
          </div>
          <span className="states__code-xl">503</span>
          <p className="states__desc">
            The compute cluster <code>gpu-pool-alpha</code> is currently unreachable.
          </p>
          <div className="states__health-row">
            <span className="label-mono">System Health:</span>
            <span className="states__health-status">DEGRADED</span>
          </div>
          <div className="states__health-bar"><div style={{ width: '38%' }} /></div>
          <span className="states__retry">RETRYING_IN: 00:14</span>
        </section>

        {/* Empty state (reuses the shared primitive) */}
        <div className="states__empty">
          <EmptyState
            icon={<span className="material-symbols-outlined">search_off</span>}
            title="0 Entities Found"
            description="No models, datasets, or jobs match your current query parameters in the selected workspace."
          />
        </div>
      </div>
    </div>
  );
}
