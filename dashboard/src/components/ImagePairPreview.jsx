import { useRef, useEffect, useState } from 'react';
import { artifactUrl } from '../api/pipeline';

export default function ImagePairPreview({ result, liveMode }) {
  const [matchesImg, setMatchesImg] = useState(null);
  const [sourceImgSrc, setSourceImgSrc] = useState(null);
  const [refImgSrc, setRefImgSrc] = useState(null);
  const [hoveredMatch, setHoveredMatch] = useState(null);

  useEffect(() => {
    if (!liveMode || !result?.runId) return;
    const arts = result.artifacts || {};
    if (arts.matches) setMatchesImg(artifactUrl(result.runId, arts.matches));
    if (arts.source) setSourceImgSrc(artifactUrl(result.runId, arts.source));
    if (arts.reference) setRefImgSrc(artifactUrl(result.runId, arts.reference));
  }, [result?.runId, liveMode]);

  const hasLiveImages = sourceImgSrc && refImgSrc;

  // Use natural image dimensions for scaling
  const srcW = result?.sourceImage?.width || 8192;
  const srcH = result?.sourceImage?.height || 8192;
  const refW = result?.referenceImage?.width || 8192;
  const refH = result?.referenceImage?.height || 8192;

  // Render dimensions for the SVG overlay
  const renderW = 410;
  const gap = 40;
  const renderSrcH = Math.round(renderW * (srcH / srcW));
  const renderRefH = Math.round(renderW * (refH / refW));
  const H = Math.max(renderSrcH, renderRefH);
  const totalW = renderW * 2 + gap;

  const sortedMatches = [...(result?.matches || [])].sort((a, b) =>
    a.inlier === b.inlier ? 0 : a.inlier ? 1 : -1
  );

  return (
    <div className="card card-large">
      <div className="card-header">
        <h3>
          Image Pair Preview
          <span className="info-icon" title="Feature matching between source and reference">i</span>
        </h3>
        {result?.matches && (
          <span className="match-count">
            <span className="dot dot-green" /> {result.matches.filter((m) => m.inlier).length} inliers
            <span className="dot dot-red" style={{ marginLeft: 10 }} /> {result.matches.filter((m) => !m.inlier).length} outliers
          </span>
        )}
      </div>

      <div className="match-canvas-container" style={{ position: 'relative', width: '100%', maxWidth: '860px', margin: '0 auto', background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
        {hasLiveImages ? (
          <div style={{ position: 'relative', width: '100%', paddingBottom: `${(H / totalW) * 100}%` }}>
            {/* Absolute positioning to scale smoothly */}
            <img src={sourceImgSrc} alt="Source" style={{ position: 'absolute', left: 0, top: `${((H - renderSrcH) / 2 / H) * 100}%`, width: `${(renderW / totalW) * 100}%`, height: `${(renderSrcH / H) * 100}%`, objectFit: 'contain' }} />
            <img src={refImgSrc} alt="Reference" style={{ position: 'absolute', left: `${((renderW + gap) / totalW) * 100}%`, top: `${((H - renderRefH) / 2 / H) * 100}%`, width: `${(renderW / totalW) * 100}%`, height: `${(renderRefH / H) * 100}%`, objectFit: 'contain' }} />
            
            <svg viewBox={`0 0 ${totalW} ${H}`} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
              {sortedMatches.map((m, i) => {
                const sx = (m.src.x / srcW) * renderW;
                const sy = (H - renderSrcH) / 2 + (m.src.y / srcH) * renderSrcH;
                const rx = renderW + gap + (m.ref.x / refW) * renderW;
                const ry = (H - renderRefH) / 2 + (m.ref.y / refH) * renderRefH;
                const color = m.inlier ? '#22c55e' : '#ef4444';
                const isHovered = hoveredMatch === i;
                
                return (
                  <g key={i} style={{ pointerEvents: 'auto', cursor: 'crosshair' }}
                     onMouseEnter={() => setHoveredMatch(i)}
                     onMouseLeave={() => setHoveredMatch(null)}>
                    <line x1={sx} y1={sy} x2={rx} y2={ry} stroke={color} strokeWidth={isHovered ? 2.5 : (m.inlier ? 1.3 : 0.8)} opacity={isHovered ? 1 : (m.inlier ? 0.7 : 0.3)} />
                    <circle cx={sx} cy={sy} r={isHovered ? 5 : 3} fill={color} opacity={isHovered ? 1 : 0.8} />
                    <circle cx={rx} cy={ry} r={isHovered ? 5 : 3} fill={color} opacity={isHovered ? 1 : 0.8} />
                  </g>
                );
              })}
            </svg>
            
            {hoveredMatch !== null && (
              <div style={{ position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(255,255,255,0.95)', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', color: '#0f172a', fontWeight: 600, pointerEvents: 'none', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                {sortedMatches[hoveredMatch].inlier ? 'Inlier Match' : 'Outlier Match'} (Conf: {sortedMatches[hoveredMatch].confidence?.toFixed(2)})
                {sortedMatches[hoveredMatch].error != null && <span> | Error: {sortedMatches[hoveredMatch].error?.toFixed(2)}px</span>}
              </div>
            )}
          </div>
        ) : matchesImg ? (
          <img src={matchesImg} alt="Matches" style={{ display: 'block', width: '100%', height: 'auto' }} />
        ) : (
          <div style={{ height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', color: '#475569', fontSize: '14px' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.5" style={{ marginBottom: '16px' }}>
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            Select a dataset and run the pipeline to visualize local satellite imagery.
          </div>
        )}
      </div>

      <div className="image-labels">
        <div className="image-label">
          <strong>{result?.sourceImage?.label || 'Source Image'}</strong>
          <span>{result?.sourceImage?.width || 0} x {result?.sourceImage?.height || 0}</span>
        </div>
        <div className="image-label">
          <strong>{result?.referenceImage?.label || 'Reference Image'}</strong>
          <span>{result?.referenceImage?.width || 0} x {result?.referenceImage?.height || 0}</span>
        </div>
      </div>
    </div>
  );
}
