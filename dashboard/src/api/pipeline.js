const API_BASE = '/api';

export async function fetchPairs() {
  const res = await fetch(`${API_BASE}/pairs`);
  if (!res.ok) throw new Error('Failed to fetch pairs');
  return res.json();
}

export async function runPipeline(config) {
  const res = await fetch(`${API_BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Pipeline failed');
  }
  return res.json();
}

export function artifactUrl(runId, name) {
  return `${API_BASE}/runs/${runId}/artifacts/${name}`;
}

export function transformResult(raw) {
  const correspondences = raw.correspondences || [];
  const inliers = correspondences.filter((c) => c.inlier);
  const outliers = correspondences.filter((c) => !c.inlier);
  const errors = correspondences.filter((c) => c.error_tmc2_px != null).map((c) => c.error_tmc2_px);
  const inlierErrors = inliers.filter((c) => c.error_tmc2_px != null).map((c) => c.error_tmc2_px);

  const regions = raw.regions || {};
  const sourceRoi = regions.source_roi_xywh || [0, 0, 8192, 8192];
  const refRoi = regions.reference_roi_xywh || [0, 0, 8192, 8192];
  const sourceGsd = regions.source_gsd_m || 0.25;
  const refGsd = regions.reference_gsd_m || 0.25;
  const sameSensor = Math.abs(sourceGsd - refGsd) < 0.5;

  const metrics = raw.metrics || {};
  const transformation = raw.transformation || null;

  let matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  let modelName = raw.config?.model || 'affine';
  if (transformation) {
    matrix = transformation.full_native_matrix || transformation.source_working_to_reference_native_roi || matrix;
    modelName = transformation.model || modelName;
  }

  const histBinSize = 0.1;
  const histMax = 2.0;
  const numBins = Math.ceil(histMax / histBinSize) + 1;
  const histogramBins = new Array(numBins).fill(0);
  const histogramLabels = Array.from({ length: numBins }, (_, i) => (i * histBinSize).toFixed(1));
  for (const e of errors) {
    const idx = Math.min(Math.floor(e / histBinSize), numBins - 1);
    histogramBins[idx]++;
  }

  const meanError = metrics.inlier_rmse_tmc2_px ?? (inlierErrors.length > 0 ? inlierErrors.reduce((a, b) => a + b, 0) / inlierErrors.length : 0);

  const totalFiltered = metrics.filtered_matches || correspondences.length;
  const inlierCount = metrics.inliers || inliers.length;
  const inlierRatio = metrics.inlier_ratio ?? (totalFiltered > 0 ? inlierCount / totalFiltered : 0);

  return {
    raw,
    runId: raw.run_id,
    pairId: raw.pair_id,
    status: raw.status,
    reason: raw.reason,
    method: raw.method || 'unknown',

    artifacts: raw.artifacts || {},

    sourceImage: {
      label: sameSensor ? `Source (${sourceGsd} m/px)` : 'OHRC (High Resolution)',
      width: sourceRoi[2],
      height: sourceRoi[3],
      resolution: `${sourceGsd} m/px`,
    },
    referenceImage: {
      label: sameSensor ? `Reference (${refGsd} m/px)` : 'TMC-2 (Medium Resolution)',
      width: refRoi[2],
      height: refRoi[3],
      resolution: `${refGsd} m/px`,
    },
    sameSensor,

    correspondences,
    matches: [...correspondences]
      .sort((a, b) => {
        if (a.inlier && !b.inlier) return -1;
        if (!a.inlier && b.inlier) return 1;
        return (b.match_confidence || 0) - (a.match_confidence || 0);
      })
      .slice(0, 200)
      .map((c) => ({
        src: { x: c.ohrc_x, y: c.ohrc_y },
        ref: { x: c.tmc2_x, y: c.tmc2_y },
        confidence: c.match_confidence,
        inlier: c.inlier,
        error: c.error_tmc2_px,
      })),

    correspondence: {
      scatterPoints: correspondences.map((c) => ({ x: c.ohrc_x, y: c.ohrc_y })),
      totalPoints: metrics.raw_match_count || correspondences.length,
      filteredPoints: totalFiltered,
      inlierCount,
      inlierRatio,
      inlierPct: (inlierRatio * 100).toFixed(1),
      outlierCount: totalFiltered - inlierCount,
      outlierPct: ((1 - inlierRatio) * 100).toFixed(1),
      meanConfidence: metrics.mean_match_confidence,
      hullCoverageSrc: metrics.source_hull_coverage,
      hullCoverageRef: metrics.reference_hull_coverage,
      overlapFraction: metrics.valid_overlap_fraction_of_reference,
    },

    reprojectionError: {
      histogramBins,
      histogramLabels,
      mean: parseFloat(meanError.toFixed(2)),
      median: metrics.inlier_median_tmc2_px,
      p95: metrics.inlier_p95_tmc2_px,
      max: metrics.inlier_max_tmc2_px,
    },

    transformation: {
      model: `${modelName.charAt(0).toUpperCase() + modelName.slice(1)} (RANSAC)`,
      matrix: matrix.map((row) => row.map((v) => parseFloat(v.toFixed(6)))),
      inliers: inlierCount,
      totalMatches: totalFiltered,
      inlierPct: (inlierRatio * 100).toFixed(1),
      reprojectionError: parseFloat(meanError.toFixed(2)),
      ransacThreshold: raw.config?.ransac_threshold,
    },

    timing: raw.elapsed_seconds,
  };
}
