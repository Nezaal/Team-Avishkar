export default function TransformationSummary({ data }) {
  if (!data) return null;

  return (
    <div className="card">
      <div className="card-header">
        <h3>Transformation Summary</h3>
      </div>
      <div className="transform-content">
        <div className="transform-row">
          <span className="transform-label">Model Used</span>
          <span className="transform-value stat-blue">{data.model}</span>
        </div>

        <div className="matrix-container">
          <table className="matrix-table">
            <tbody>
              {data.matrix.map((row, i) => (
                <tr key={i}>
                  {row.map((val, j) => {
                    const s = typeof val === 'number' ? formatMatrixVal(val) : val;
                    return <td key={j}>{s}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="transform-stats">
          <div className="transform-row">
            <span className="transform-label">Inliers</span>
            <span className="transform-value">
              {data.inliers?.toLocaleString()} / {data.totalMatches?.toLocaleString()}{' '}
              <span className="stat-green">({data.inlierPct}%)</span>
            </span>
          </div>
          <div className="transform-row">
            <span className="transform-label">RMSE</span>
            <span className="transform-value">{data.reprojectionError} px</span>
          </div>
          {data.ransacThreshold != null && (
            <div className="transform-row">
              <span className="transform-label">RANSAC Threshold</span>
              <span className="transform-value">{data.ransacThreshold} px</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatMatrixVal(v) {
  if (Math.abs(v) < 0.0001 && v !== 0) return v.toExponential(1);
  if (Math.abs(v) >= 100) return v.toFixed(2);
  return v.toFixed(4);
}
