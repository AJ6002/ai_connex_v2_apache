import { Button } from '@/components/ui';
import { AsyncState } from '@/components/AsyncState';
import { useWorkspaceInfo } from '@/entities/workspace/hooks';
import './WorkspaceConfigView.css';

/** Workspace Configuration — faithful to STITCH-Design/ai_connex_admin_workspace_configuration. */
export function WorkspaceConfigView() {
  const { data: workspace, isLoading, isError, error } = useWorkspaceInfo();
  const policy = workspace?.policies;
  const tenant = workspace?.tenant;

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {workspace && (
        <div className="wsc">
          <div>
            <div className="wsc__badges">
              <span className="wsc__badge wsc__badge--admin">ADMIN SCOPE</span>
              <span className="wsc__badge">REGION: {workspace.primaryRegion?.split(' ')[0] ?? '—'}</span>
            </div>
            <h1 className="wsc__title" style={{ marginTop: 12 }}>Workspace Configuration</h1>
            <p className="wsc__sub">
              Manage core identity, tenant boundaries, and global platform policies for this environment.
            </p>
          </div>

          <div className="wsc__grid">
            {/* Workspace Identity */}
            <section className="wsc__panel">
              <div className="wsc__panel-head">
                <span className="wsc__panel-title">
                  <span className="material-symbols-outlined">badge</span> Workspace Identity
                </span>
                <Button variant="secondary" size="sm">Edit Details</Button>
              </div>
              <div className="wsc__field-grid">
                <div className="wsc__field">
                  <span className="label-mono">WORKSPACE NAME</span>
                  <div className="wsc__field-box"><span>{workspace.name}</span></div>
                </div>
                <div className="wsc__field">
                  <span className="label-mono">WORKSPACE ID</span>
                  <div className="wsc__field-box">
                    <span className="wsc__field-mono">{workspace.workspaceId}</span>
                    <button type="button" aria-label="Copy workspace id"><span className="material-symbols-outlined">content_copy</span></button>
                  </div>
                </div>
                <div className="wsc__field">
                  <span className="label-mono">PRIMARY REGION</span>
                  <div className="wsc__field-box">
                    <span><span className="material-symbols-outlined">location_on</span>{workspace.primaryRegion}</span>
                  </div>
                </div>
                <div className="wsc__field">
                  <span className="label-mono">CREATED DATE</span>
                  <div className="wsc__field-box"><span className="wsc__field-mono">{workspace.createdAt}</span></div>
                </div>
              </div>
            </section>

            {/* Tenant Config */}
            <section className="wsc__panel">
              <span className="wsc__panel-title" style={{ marginBottom: 20, display: 'block' }}>
                <span className="material-symbols-outlined">domain</span> Tenant Config
              </span>
              <div className="wsc__tenant-cards">
                <div className="wsc__tcard">
                  <div className="wsc__tcard-head">
                    <span className="label-mono">PRIVACY MODE</span>
                    {tenant?.privacyModeActive && <span className="wsc__tcard-active">ACTIVE</span>}
                  </div>
                  <span className="wsc__tcard-value">Private Cloud</span>
                  <p className="wsc__tcard-desc">Isolated compute and network topology.</p>
                </div>
                <div className="wsc__tcard">
                  <div className="wsc__tcard-head">
                    <span className="label-mono">DATA RESIDENCY</span>
                    <span className="material-symbols-outlined wsc__tcard-lock">lock</span>
                  </div>
                  <span className="wsc__tcard-value">{tenant?.dataResidency}</span>
                  <p className="wsc__tcard-desc">Cross-region replication disabled.</p>
                </div>
              </div>
            </section>

            {/* Platform Policies */}
            <section className="wsc__panel wsc__policies">
              <div className="wsc__panel-head">
                <span className="wsc__panel-title">
                  <span className="material-symbols-outlined">verified_user</span> Platform Policies
                </span>
                <Button variant="primary" size="sm" leftIcon={<span className="material-symbols-outlined">check</span>}>Apply Changes</Button>
              </div>
              <div className="wsc__policy-grid">
                <div>
                  <span className="label-mono wsc__policy-label">
                    <span className="material-symbols-outlined">info</span> AUTO-QUARANTINE THRESHOLDS
                  </span>
                  <div className="wsc__range-row">
                    <span>0.0</span>
                    <strong>{policy?.autoQuarantineThreshold.toFixed(2)} (Current)</strong>
                    <span>1.0</span>
                  </div>
                  <div className="wsc__slider-track">
                    <div style={{ width: `${(policy?.autoQuarantineThreshold ?? 0) * 100}%` }} />
                  </div>
                  <div className="wsc__strictness-row">
                    <span className="label-mono">Strictness Level</span>
                    <span className="wsc__strictness-select">
                      {policy?.strictnessLevel === 'HIGH' ? 'High (0.85)' : policy?.strictnessLevel}
                      <span className="material-symbols-outlined">expand_more</span>
                    </span>
                  </div>
                </div>
                <div>
                  <span className="label-mono wsc__policy-label">
                    <span className="material-symbols-outlined">info</span> GLOBAL MODEL RETENTION
                  </span>
                  <div className="wsc__retention-box">
                    <div className="wsc__retention-num">{policy?.modelRetentionDays}</div>
                    <span className="wsc__retention-days">DAYS</span>
                  </div>
                  <label className="wsc__checkbox-row">
                    <input type="checkbox" defaultChecked={policy?.autoArchiveBeforeDeletion} />
                    Auto-archive to cold storage before deletion
                  </label>
                </div>
              </div>
            </section>
          </div>
        </div>
      )}
    </AsyncState>
  );
}
