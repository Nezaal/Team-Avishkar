import { useState, useRef, useEffect } from 'react';
import { artifactUrl } from '../api/pipeline';

export default function RegistrationResult({ result, liveMode, isSuccess }) {
  const [sliderPos, setSliderPos] = useState(50);
  const isDragging = useRef(false);
  const containerRef = useRef(null);
  const [refUrl, setRefUrl] = useState(null);
  const [overlayUrl, setOverlayUrl] = useState(null);
  const [checkerUrl, setCheckerUrl] = useState(null);
  const [viewMode, setViewMode] = useState('overlay');

  useEffect(() => {
    if (!liveMode || !result?.runId) {
      setRefUrl(null);
      setOverlayUrl(null);
      setCheckerUrl(null);
      return;
    }
    const arts = result.artifacts || {};
    if (arts.reference) setRefUrl(artifactUrl(result.runId, arts.reference));
    if (arts.overlay) setOverlayUrl(artifactUrl(result.runId, arts.overlay));
    if (arts.checkerboard) setCheckerUrl(artifactUrl(result.runId, arts.checkerboard));
  }, [result?.runId, liveMode]);

  const handleMouseDown = () => { isDragging.current = true; };
  const handleMouseUp = () => { isDragging.current = false; };
  const handleMove = (e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    setSliderPos(Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100)));
  };

  const hasLiveImages = refUrl && (overlayUrl || checkerUrl);
  const beforeSrc = refUrl;
  const afterSrc = viewMode === 'checker' ? checkerUrl : overlayUrl;

  const statusConfig = {
    REGISTERED_UNVERIFIED: { label: 'Registration Successful', cls: 'status-success', icon: 'check' },
    LOW_CONFIDENCE: { label: 'Low Confidence Registration', cls: 'status-warn', icon: 'warn' },
    FAILED: { label: 'Registration Failed', cls: 'status-fail', icon: 'x' },
    SUCCESS: { label: 'Registration Successful', cls: 'status-success', icon: 'check' },
  };
  const st = statusConfig[result?.status] || statusConfig.FAILED;

  return (
    <div className="card">
      <div className="card-header">
        <h3>
          Registration Result
          <span className="info-icon" title="Before/after comparison of aligned images">i</span>
        </h3>
        {hasLiveImages && overlayUrl && checkerUrl && (
          <div className="view-toggle">
            <button className={viewMode === 'overlay' ? 'active' : ''} onClick={() => setViewMode('overlay')}>Overlay</button>
            <button className={viewMode === 'checker' ? 'active' : ''} onClick={() => setViewMode('checker')}>Checker</button>
          </div>
        )}
      </div>

      <div
        ref={containerRef}
        className="comparison-slider"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onMouseMove={handleMove}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
        onTouchMove={handleMove}
      >
        <div className="comparison-container">
          {hasLiveImages ? (
            <>
              <img src={beforeSrc} className="comparison-img" alt="Reference" draggable={false} />
              <div className="comparison-overlay" style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}>
                <img src={afterSrc} className="comparison-img" alt="Registered overlay" draggable={false} />
              </div>
            </>
          ) : (
            <div className="placeholder-comparison">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
              <span>Run pipeline to see before/after comparison</span>
            </div>
          )}
          <div className="slider-line" style={{ left: `${sliderPos}%` }}>
            <div className="slider-handle">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M9 18l-6-6 6-6" /><path d="M15 6l6 6-6 6" />
              </svg>
            </div>
          </div>
          <span className="comparison-label label-before">Reference</span>
          <span className="comparison-label label-after">Registered</span>
        </div>
      </div>

      <div className={`registration-status ${st.cls}`}>
        {st.icon === 'check' && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#16a34a" />
            <path d="M8 12l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
        {st.icon === 'warn' && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#d97706" />
            <path d="M12 8v4m0 4h.01" stroke="white" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )}
        {st.icon === 'x' && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#dc2626" />
            <path d="M8 8l8 8M16 8l-8 8" stroke="white" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )}
        <span>{st.label}</span>
        {result?.reason && <span className="status-reason">— {result.reason}</span>}
      </div>
    </div>
  );
}
