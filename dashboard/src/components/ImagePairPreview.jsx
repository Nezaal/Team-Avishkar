import { useRef, useEffect, useState } from 'react';
import { artifactUrl } from '../api/pipeline';

export default function ImagePairPreview({ result, liveMode }) {
  const canvasRef = useRef(null);
  const [matchesImg, setMatchesImg] = useState(null);
  const [sourceImg, setSourceImg] = useState(null);
  const [refImg, setRefImg] = useState(null);

  useEffect(() => {
    if (!liveMode || !result?.runId) return;
    const arts = result.artifacts || {};
    if (arts.matches) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => setMatchesImg(img);
      img.src = artifactUrl(result.runId, arts.matches);
    }
    if (arts.source) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => setSourceImg(img);
      img.src = artifactUrl(result.runId, arts.source);
    }
    if (arts.reference) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => setRefImg(img);
      img.src = artifactUrl(result.runId, arts.reference);
    }
  }, [result?.runId, liveMode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (matchesImg) {
      const aspect = matchesImg.width / matchesImg.height;
      canvas.width = 860;
      canvas.height = Math.round(860 / aspect);
      ctx.drawImage(matchesImg, 0, 0, canvas.width, canvas.height);
      return;
    }

    if (sourceImg && refImg) {
      const imgW = 410;
      const gap = 40;
      const srcH = Math.round(imgW * (sourceImg.height / sourceImg.width));
      const refH = Math.round(imgW * (refImg.height / refImg.width));
      const H = Math.max(srcH, refH);
      canvas.width = imgW * 2 + gap;
      canvas.height = H;
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(sourceImg, 0, (H - srcH) / 2, imgW, srcH);
      ctx.drawImage(refImg, imgW + gap, (H - refH) / 2, imgW, refH);
      drawMatchLines(ctx, result, imgW, gap, srcH, refH, H);
      return;
    }

    canvas.width = 860;
    canvas.height = 380;
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, 860, 380);
    drawProceduralMoon(ctx, 5, 5, 405, 370, 42);
    drawProceduralMoon(ctx, 450, 5, 405, 370, 99);
    drawMatchLines(ctx, result, 405, 40, 370, 370, 380);
  }, [matchesImg, sourceImg, refImg, result]);

  return (
    <div className="card card-large">
      <div className="card-header">
        <h3>
          Image Pair Preview
          <span className="info-icon" title="Feature matching between OHRC source and TMC-2 reference">i</span>
        </h3>
        {result?.matches && (
          <span className="match-count">
            <span className="dot dot-green" /> {result.matches.filter((m) => m.inlier).length} inliers
            <span className="dot dot-red" style={{ marginLeft: 10 }} /> {result.matches.filter((m) => !m.inlier).length} outliers
          </span>
        )}
      </div>
      <canvas ref={canvasRef} className="match-canvas" />
      <div className="image-labels">
        <div className="image-label">
          <strong>{result?.sourceImage?.label || 'OHRC (High Resolution)'}</strong>
          <span>{result?.sourceImage?.width} x {result?.sourceImage?.height} &bull; {result?.sourceImage?.resolution}</span>
        </div>
        <div className="image-label">
          <strong>{result?.referenceImage?.label || 'TMC-2 (Medium Resolution)'}</strong>
          <span>{result?.referenceImage?.width} x {result?.referenceImage?.height} &bull; {result?.referenceImage?.resolution}</span>
        </div>
      </div>
    </div>
  );
}

function drawMatchLines(ctx, result, imgW, gap, srcH, refH, H) {
  if (!result?.matches) return;
  const srcMaxX = Math.max(...result.matches.map((m) => m.src.x), 1);
  const srcMaxY = Math.max(...result.matches.map((m) => m.src.y), 1);
  const refMaxX = Math.max(...result.matches.map((m) => m.ref.x), 1);
  const refMaxY = Math.max(...result.matches.map((m) => m.ref.y), 1);

  for (const m of result.matches) {
    const sx = 5 + (m.src.x / srcMaxX) * (imgW - 10);
    const sy = (H - srcH) / 2 + 5 + (m.src.y / srcMaxY) * (srcH - 10);
    const rx = imgW + gap + (m.ref.x / refMaxX) * (imgW - 10);
    const ry = (H - refH) / 2 + 5 + (m.ref.y / refMaxY) * (refH - 10);

    const color = m.inlier ? '#22c55e' : '#ef4444';

    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(rx, ry);
    ctx.strokeStyle = color;
    ctx.globalAlpha = m.inlier ? 0.7 : 0.3;
    ctx.lineWidth = m.inlier ? 1.3 : 0.8;
    ctx.stroke();
    ctx.globalAlpha = 1;

    for (const [px, py] of [[sx, sy], [rx, ry]]) {
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }
}

function drawProceduralMoon(ctx, ox, oy, w, h, seed) {
  let s = seed;
  const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  ctx.save();
  ctx.beginPath();
  ctx.rect(ox, oy, w, h);
  ctx.clip();
  ctx.fillStyle = '#2a2a2a';
  ctx.fillRect(ox, oy, w, h);
  for (let i = 0; i < 15; i++) {
    const cx = ox + r() * w, cy = oy + r() * h, cr = 8 + r() * 40;
    ctx.beginPath();
    ctx.arc(cx, cy, cr, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(100,100,100,${0.3 + r() * 0.3})`;
    ctx.lineWidth = 1.2;
    ctx.stroke();
    const g = ctx.createRadialGradient(cx - cr * 0.2, cy - cr * 0.2, 0, cx, cy, cr);
    g.addColorStop(0, 'rgba(60,60,60,0.2)');
    g.addColorStop(1, 'rgba(20,20,20,0.4)');
    ctx.fillStyle = g;
    ctx.fill();
  }
  for (let i = 0; i < 300; i++) {
    ctx.fillStyle = `rgba(${50 + r() * 50},${50 + r() * 50},${50 + r() * 50},0.4)`;
    ctx.fillRect(ox + r() * w, oy + r() * h, 1 + r() * 3, 1 + r() * 3);
  }
  ctx.restore();
}
