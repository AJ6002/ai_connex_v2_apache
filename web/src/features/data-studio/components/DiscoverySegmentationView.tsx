import { AsyncState } from '@/components/AsyncState';
import { useDiscoveryArtifact, useReviewDiscoverySegment } from '@/entities/dataset/hooks';
import type { DiscoverySegment } from '@/entities/dataset/types';
import './DiscoverySegmentationView.css';

interface Props {
  assetId: string;
}

/** Discovery & Segmentation Review — faithful to STITCH-Design/ai_connex_discovery_segmentation_review. */
export function DiscoverySegmentationView({ assetId }: Props) {
  const { data: artifact, isLoading, isError, error } = useDiscoveryArtifact(assetId);
  const review = useReviewDiscoverySegment(assetId);

  const segments = artifact?.segments ?? [];
  const pendingCount = segments.filter((s) => s.reviewStatus === 'PENDING').length;

  return (
    <AsyncState isLoading={isLoading} isError={isError} error={error}>
      {artifact && (
        <div className="disco">
          {/* ── Header ───────────────────────────────────────────────────── */}
          <header className="disco__header">
            <div>
              <h1 className="disco__title">Discovery &amp; Segmentation</h1>
              <p className="disco__meta label-mono">
                FILE: {artifact.fileName} | SIZE: {artifact.fileSizeLabel}
              </p>
            </div>
            <div className="disco__status">
              <span className="label-mono">STATUS</span>
              <span className={`disco__status-value${pendingCount === 0 ? ' disco__status-value--done' : ''}`}>
                <span className="disco__status-dot" />
                {pendingCount === 0 ? 'Review Complete' : 'Awaiting Approval'}
              </span>
            </div>
          </header>

          {/* ── Discovery map ────────────────────────────────────────────── */}
          <section className="disco__map">
            <div className="disco__map-head">
              <span className="label-mono">DISCOVERY_MAP_VIEW</span>
              <div className="disco__map-tools">
                <span className="material-symbols-outlined">zoom_in</span>
                <span className="material-symbols-outlined">zoom_out</span>
                <span className="material-symbols-outlined">fullscreen</span>
              </div>
            </div>
            <div className="disco__map-canvas">
              {segments.map((seg) => (
                <SegmentTile key={seg.segmentId} segment={seg} />
              ))}
            </div>
          </section>

          {/* ── Review cards ─────────────────────────────────────────────── */}
          <div className="disco__reviews">
            {segments
              .filter((s) => s.sampleRows.length > 0)
              .map((seg) => (
                <div
                  key={seg.segmentId}
                  className={`disco__review disco__review--${seg.ambiguous ? 'amber' : 'cyan'}${
                    seg.reviewStatus !== 'PENDING' ? ' disco__review--decided' : ''
                  }`}
                >
                  <div className="disco__review-head">
                    <span className="label-mono">SEGMENT {seg.segmentId.replace('SEG_', '')}</span>
                    <span className={`disco__conf disco__conf--${seg.ambiguous ? 'amber' : 'cyan'}`}>
                      <span className="material-symbols-outlined">
                        {seg.ambiguous ? 'warning' : 'check_circle'}
                      </span>
                      {seg.confidencePct}% CONF
                    </span>
                  </div>
                  <h2 className="disco__review-name">
                    {seg.name}
                    {seg.ambiguous && <span className="disco__ambiguous"> (Ambiguous)</span>}
                  </h2>
                  <div className="disco__review-footer">
                    <span className="label-mono disco__review-stats">
                      ROWS: {seg.estimatedRows}
                      <br />
                      COLS: {seg.estimatedCols}
                    </span>
                    {seg.reviewStatus === 'PENDING' ? (
                      <div className="disco__review-actions">
                        <button
                          type="button"
                          className="disco__reject"
                          disabled={review.isPending}
                          onClick={() => review.mutate({ segmentId: seg.segmentId, decision: 'REJECTED' })}
                        >
                          REJECT
                        </button>
                        <button
                          type="button"
                          className={`disco__approve disco__approve--${seg.ambiguous ? 'amber' : 'cyan'}`}
                          disabled={review.isPending}
                          onClick={() => review.mutate({ segmentId: seg.segmentId, decision: 'APPROVED' })}
                        >
                          APPROVE
                        </button>
                      </div>
                    ) : (
                      <span className={`disco__decision disco__decision--${seg.reviewStatus.toLowerCase()}`}>
                        {seg.reviewStatus}
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </AsyncState>
  );
}

function SegmentTile({ segment }: { segment: DiscoverySegment }) {
  const tone = segment.confidencePct >= 90 ? 'cyan' : segment.confidencePct >= 40 ? 'amber' : 'muted';
  return (
    <div className={`disco__tile disco__tile--${tone}`}>
      <div className="disco__tile-head">
        <span>
          {segment.segmentId}: {segment.name}
        </span>
        <span>CONF: {segment.confidencePct}%</span>
      </div>
      <pre className="disco__tile-body">{segment.sampleRows.join('\n')}</pre>
    </div>
  );
}
