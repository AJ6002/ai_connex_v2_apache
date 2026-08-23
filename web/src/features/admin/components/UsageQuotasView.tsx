import { AsyncState } from '@/components/AsyncState';
import { useWorkspaceInfo } from '@/entities/workspace/hooks';
import './UsageQuotasView.css';

const RING_R = 60;
const RING_C = 2 * Math.PI * RING_R;

/** Usage & Quotas — faithful to STITCH-Design/ai_connex_admin_usage_quotas. */
export function UsageQuotasView() {
  const { data: workspace, isLoading, isError, error } = useWorkspaceInfo();
  const q = workspace?.quotas;

  const billingPct = q ? Math.min(100, (q.billingEstimateUsd! / q.billingLimitUsd!) * 100) : 0;
  const gpuPct = q ? Math.min(1, q.gpuHoursUsed / q.gpuHoursQuota) : 0;
  const hotPct = q?.storageHotLimitTb ? (q.storageHotUsedTb! / q.storageHotLimitTb) * 100 : 0;
  const coldPct = q?.storageColdLimitTb ? (q.storageColdUsedTb! / q.storageColdLimitTb) * 100 : 0;

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      <div className="quota">
        <header className="quota__header">
          <p className="quota__sub">Monitor resource consumption and budget thresholds.</p>
          <span className="quota__cycle">CYCLE ENDS IN {q?.billingCycleEndsInDays ?? '—'} DAYS</span>
        </header>

        <div className="quota__grid">
          {/* Billing */}
          <section className="quota__panel">
            <div className="quota__panel-head">
              <span className="label-mono">CURRENT BILLING CYCLE</span>
              <span className="material-symbols-outlined">credit_card</span>
            </div>
            <span className="quota__amount">Est. total: ${q?.billingEstimateUsd?.toLocaleString() ?? '—'}.00</span>
            <div className="quota__bar-row">
              <span className="quota__bar-label">${q?.billingLimitUsd?.toLocaleString() ?? '—'}</span>
              <div className="quota__bar"><div style={{ width: `${billingPct}%` }} /></div>
            </div>
          </section>

          {/* Compute */}
          <section className="quota__panel">
            <div className="quota__panel-head">
              <span className="label-mono">COMPUTE (A100 GPUS)</span>
              <span className="material-symbols-outlined">memory</span>
            </div>
            <div className="quota__ring-wrap">
              <svg viewBox="0 0 140 140" className="quota__ring">
                <circle className="quota__ring-track" cx="70" cy="70" r={RING_R} />
                <circle
                  className="quota__ring-fill"
                  cx="70"
                  cy="70"
                  r={RING_R}
                  strokeDasharray={`${RING_C * gpuPct} ${RING_C}`}
                />
              </svg>
              <div className="quota__ring-legend">
                <span>USED: <strong>{q?.gpuHoursUsed}H</strong></span>
                <span>LIMIT: <strong>{q?.gpuHoursQuota}H</strong></span>
              </div>
            </div>
          </section>

          {/* Storage */}
          <section className="quota__panel">
            <div className="quota__panel-head">
              <span className="label-mono">STORAGE</span>
              <span className="material-symbols-outlined">database</span>
            </div>
            <div className="quota__storage-rows">
              <div className="quota__bar-row">
                <span className="quota__bar-label">{q?.storageHotUsedTb} TB / {q?.storageHotLimitTb} TB</span>
                <div className="quota__bar"><div style={{ width: `${hotPct}%` }} /></div>
              </div>
              <div className="quota__bar-row">
                <span className="quota__bar-label">{q?.storageColdUsedTb} TB / {q?.storageColdLimitTb} TB</span>
                <div className="quota__bar"><div style={{ width: `${coldPct}%`, backgroundColor: 'var(--color-inverse-primary)' }} /></div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </AsyncState>
  );
}
