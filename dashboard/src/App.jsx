import { useState, useCallback } from 'react';
import ImagePairPreview from './components/ImagePairPreview';
import RegistrationResult from './components/RegistrationResult';
import CorrespondenceDistribution from './components/CorrespondenceDistribution';
import ReprojectionError from './components/ReprojectionError';
import TransformationSummary from './components/TransformationSummary';
import PipelineConfig from './components/PipelineConfig';
import MetricsBanner from './components/MetricsBanner';
import { runPipeline, transformResult } from './api/pipeline';

const DEFAULT_CONFIG = {
  pair_id: 'pair_020',
  device: 'cpu',
  model: 'affine',
  ransac_threshold: 5.0,
  min_confidence: 0.5,
  max_size: 512,
  source_side: 4096,
  source_roi: [0, 0, 4096, 4096],
  reference_roi: [0, 0, 4096, 4096]
};

export default function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [liveMode, setLiveMode] = useState(false);

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const raw = await runPipeline(config);
      const transformed = transformResult(raw);
      setResult(transformed);
      setLiveMode(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [config]);

  const isSuccess = result?.status === 'REGISTERED_UNVERIFIED' || result?.status === 'SUCCESS';

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32">
              <circle cx="16" cy="16" r="14" fill="#0f172a" stroke="#16a34a" strokeWidth="2" />
              <circle cx="11" cy="11" r="3.5" fill="none" stroke="#334155" strokeWidth="1.2" />
              <circle cx="20" cy="19" r="5" fill="none" stroke="#334155" strokeWidth="1.2" />
              <circle cx="7" cy="21" r="2" fill="none" stroke="#334155" strokeWidth="1" />
              <line x1="6" y1="16" x2="26" y2="16" stroke="#16a34a" strokeWidth="0.5" opacity="0.4" />
            </svg>
          </div>
          <div>
            <h1>ChandraMatch</h1>
            <p className="header-subtitle">Chandrayaan-2 OHRC / TMC-2 Co-Registration</p>
          </div>
        </div>
        <div className="header-actions">
          {result?.timing && (
            <span className="timing-badge">{result.timing}s</span>
          )}
          <button className="run-btn" onClick={handleRun} disabled={loading}>
            {loading ? (
              <><span className="spinner" /> Running...</>
            ) : (
              <>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
                Run Pipeline
              </>
            )}
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
          </svg>
          <span>{error}</span>
          <button onClick={() => setError(null)}>&times;</button>
        </div>
      )}

      <div className="config-strip">
        <PipelineConfig config={config} onChange={setConfig} disabled={loading} />
      </div>

      {result && <MetricsBanner result={result} isSuccess={isSuccess} />}

      <main className="dashboard-grid">
        <div className="row-top">
          <ImagePairPreview result={result} liveMode={liveMode} />
          <RegistrationResult result={result} liveMode={liveMode} isSuccess={isSuccess} />
        </div>
        <div className="row-bottom">
          <CorrespondenceDistribution data={result?.correspondence} correspondences={result?.correspondences} sourceImage={result?.sourceImage} />
          <ReprojectionError data={result?.reprojectionError} />
          <TransformationSummary data={result?.transformation} />
        </div>
      </main>
    </div>
  );
}
