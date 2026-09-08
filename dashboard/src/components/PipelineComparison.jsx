export default function PipelineComparison() {
  const data = [
    { name: 'SIFT (Baseline)', raw: 6870, inliers: 776, inlierRatio: '11.29%', rmse: '1.80' },
    { name: 'LoFTR (Transformer)', raw: 10086, inliers: 973, inlierRatio: '10.69%', rmse: '1.95' },
    { name: 'SuperPoint + LightGlue', raw: 1080, inliers: 50, inlierRatio: '4.78%', rmse: '1.97' },
  ];

  return (
    <div className="card" style={{ marginTop: '20px' }}>
      <h3 style={{ marginBottom: '15px', color: '#15243b' }}>Algorithm Registration Performance (pair_020)</h3>
      <div style={{ display: 'flex', gap: '20px' }}>
        {data.map((algo) => (
          <div key={algo.name} style={{ flex: 1, backgroundColor: '#f4f6fa', padding: '15px', borderRadius: '8px', border: '1px solid #e1e4eb' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '18px', color: '#2563eb' }}>{algo.name}</h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span style={{ color: '#64748b' }}>Raw Matches:</span>
              <span style={{ fontWeight: '600' }}>{algo.raw}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span style={{ color: '#64748b' }}>RANSAC Inliers:</span>
              <span style={{ fontWeight: '600', color: '#16a34a' }}>{algo.inliers}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span style={{ color: '#64748b' }}>Inlier Ratio:</span>
              <span style={{ fontWeight: '600' }}>{algo.inlierRatio}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #cbd5e1' }}>
              <span style={{ color: '#64748b', fontWeight: 'bold' }}>Reprojection RMSE:</span>
              <span style={{ fontWeight: 'bold' }}>{algo.rmse} px</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
