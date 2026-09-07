const MATCH_COLORS = [
  '#f97316', '#3b82f6', '#22c55e', '#eab308', '#ec4899',
  '#8b5cf6', '#06b6d4', '#ef4444', '#14b8a6', '#f59e0b',
];

function rng(seed) {
  let s = seed;
  return () => { s = (s * 16807 + 0) % 2147483647; return s / 2147483647; };
}

function genCorrespondences(count) {
  const r = rng(42);
  const out = [];
  for (let i = 0; i < count; i++) {
    const inlier = r() > 0.34;
    const err = inlier ? Math.abs(0.3 + (r() - 0.5) * 0.4) : 1.5 + r() * 3;
    out.push({
      ohrc_x: r() * 8000 + 100,
      ohrc_y: r() * 8000 + 100,
      tmc2_x: r() * 700 + 20,
      tmc2_y: r() * 680 + 20,
      match_confidence: 0.3 + r() * 0.65,
      inlier,
      error_tmc2_px: inlier ? err : err,
    });
  }
  return out;
}

const correspondences = genCorrespondences(320);
const inliers = correspondences.filter((c) => c.inlier);
const inlierErrors = inliers.map((c) => c.error_tmc2_px);
const meanErr = inlierErrors.reduce((a, b) => a + b, 0) / inlierErrors.length;

function buildHist(errors) {
  const bins = new Array(22).fill(0);
  const labels = Array.from({ length: 22 }, (_, i) => (i * 0.1).toFixed(1));
  for (const e of errors) bins[Math.min(Math.floor(e / 0.1), 21)]++;
  return { bins, labels };
}
const { bins, labels } = buildHist(correspondences.map((c) => c.error_tmc2_px));

export const MOCK_RESULT = {
  raw: null,
  runId: null,
  pairId: 'pair_001',
  status: 'REGISTERED_UNVERIFIED',
  reason: null,
  method: 'superpoint_lightglue',
  artifacts: {},

  sourceImage: {
    label: 'OHRC (High Resolution)',
    width: 8192,
    height: 8192,
    resolution: '0.25 m/px',
  },
  referenceImage: {
    label: 'TMC-2 (Medium Resolution)',
    width: 744,
    height: 714,
    resolution: '4.48 m/px',
  },

  correspondences,
  matches: correspondences.slice(0, 100).map((c) => ({
    src: { x: c.ohrc_x, y: c.ohrc_y },
    ref: { x: c.tmc2_x, y: c.tmc2_y },
    confidence: c.match_confidence,
    inlier: c.inlier,
    error: c.error_tmc2_px,
  })),

  correspondence: {
    scatterPoints: correspondences.map((c) => ({ x: c.ohrc_x, y: c.ohrc_y })),
    totalPoints: 468,
    filteredPoints: 320,
    inlierCount: inliers.length,
    inlierRatio: inliers.length / 320,
    inlierPct: ((inliers.length / 320) * 100).toFixed(1),
    outlierCount: 320 - inliers.length,
    outlierPct: (((320 - inliers.length) / 320) * 100).toFixed(1),
    meanConfidence: 0.63,
    hullCoverageSrc: 0.72,
    hullCoverageRef: 0.58,
    overlapFraction: 0.45,
  },

  reprojectionError: {
    histogramBins: bins,
    histogramLabels: labels,
    mean: parseFloat(meanErr.toFixed(2)),
    median: 0.32,
    p95: 0.89,
    max: 1.42,
  },

  transformation: {
    model: 'Affine (RANSAC)',
    matrix: [
      [0.9987, -0.0482, 15.2371],
      [0.0469, 0.9989, -11.4827],
      [0.000001, 0.000002, 1.0],
    ],
    inliers: inliers.length,
    totalMatches: 320,
    inlierPct: ((inliers.length / 320) * 100).toFixed(1),
    reprojectionError: parseFloat(meanErr.toFixed(2)),
    ransacThreshold: 5.0,
  },

  timing: 4.231,
};
