export default function MetricsBanner({ result, isSuccess }) {
  if (!result) return null;
  const c = result.correspondence || {};
  const t = result.transformation || {};
  const r = result.reprojectionError || {};

  const statusLabel = {
    REGISTERED_UNVERIFIED: 'Registered',
    LOW_CONFIDENCE: 'Low Confidence',
    FAILED: 'Failed',
    SUCCESS: 'Registered',
  }[result.status] || result.status;

  return (
    <div className={`metrics-banner ${isSuccess ? 'banner-success' : 'banner-fail'}`}>
      <div className="metric-tile">
        <span className="metric-value-lg">{statusLabel}</span>
        <span className="metric-label">Status</span>
      </div>
      <div className="metric-divider" />
      <div className="metric-tile">
        <span className="metric-value-lg">{c.totalPoints || '—'}</span>
        <span className="metric-label">Raw Matches</span>
      </div>
      <div className="metric-tile">
        <span className="metric-value-lg">{c.filteredPoints || '—'}</span>
        <span className="metric-label">Filtered</span>
      </div>
      <div className="metric-tile">
        <span className="metric-value-lg highlight-green">{c.inlierCount || '—'}</span>
        <span className="metric-label">Inliers ({c.inlierPct || 0}%)</span>
      </div>
      <div className="metric-divider" />
      <div className="metric-tile">
        <span className="metric-value-lg">{r.mean || '—'} <small>px</small></span>
        <span className="metric-label">RMSE</span>
      </div>
      {r.median != null && (
        <div className="metric-tile">
          <span className="metric-value-lg">{r.median.toFixed(2)} <small>px</small></span>
          <span className="metric-label">Median Error</span>
        </div>
      )}
      {c.hullCoverageSrc != null && (
        <>
          <div className="metric-divider" />
          <div className="metric-tile">
            <span className="metric-value-lg">{(c.hullCoverageSrc * 100).toFixed(0)}%</span>
            <span className="metric-label">Src Coverage</span>
          </div>
          <div className="metric-tile">
            <span className="metric-value-lg">{(c.hullCoverageRef * 100).toFixed(0)}%</span>
            <span className="metric-label">Ref Coverage</span>
          </div>
        </>
      )}
      {c.overlapFraction != null && (
        <div className="metric-tile">
          <span className="metric-value-lg">{(c.overlapFraction * 100).toFixed(0)}%</span>
          <span className="metric-label">Overlap</span>
        </div>
      )}
    </div>
  );
}
