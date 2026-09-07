"""One local region per run. All coordinate transforms are explicitly composed."""
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import time
import uuid

import cv2
import numpy as np

from .artifacts import write_artifacts, write_image
from .data import ROOT, TileStore, centered_roi
from .geometry import (GeoGrid, fetch_grid, locate_reference, normalize, resize_matrix,
                       transform_points, translation)
from .matching import LoFTRMatcher, estimate, filter_matches, hull_coverage, residual_metrics

LOG = logging.getLogger(__name__)


@dataclass
class RunConfig:
    pair_id: str = "pair_001"
    repo_id: str = "akshitjn/my-large-dataset"
    revision: str = "main"
    geometry_repo: str = "Nezaal/pradan-dataset"
    geometry_revision: str = "main"
    local_root: str | None = None
    offline: bool = False
    cache_dir: str = "C:/hfcache"
    output_root: str = str(ROOT / "dataset/loftr_runs")
    source_roi: list[int] | None = None
    reference_roi: list[int] | None = None
    source_side: int = 8192
    max_size: int = 512
    reference_margin: int = 128
    min_confidence: float = .5
    ransac_threshold: float = 2.
    model: str = "affine"
    device: str = "auto"
    checkpoint: str | None = None
    clahe: bool = False
    workers: int = 6
    threads: int = 4

    def __post_init__(self):
        if not 128 <= self.max_size <= 1024:
            raise ValueError("max_size must be 128..1024")
        if not 1024 <= self.source_side <= 12000:
            raise ValueError("source_side must be 1024..12000 native OHRC pixels")
        if not 0 <= self.min_confidence <= 1 or not 0 < self.ransac_threshold <= 10:
            raise ValueError("Invalid confidence or RANSAC threshold")
        if self.model not in ("affine", "homography") or self.device not in ("auto", "cpu", "cuda"):
            raise ValueError("Unsupported model or device")
        if not 1 <= self.workers <= 16 or not 1 <= self.threads <= 32:
            raise ValueError("Invalid worker/thread count")
        if not 16 <= self.reference_margin <= 512:
            raise ValueError("reference_margin must be 16..512")
        for roi in (self.source_roi, self.reference_roi):
            if roi is not None and (len(roi) != 4 or any(not isinstance(v, int) for v in roi)
                                    or min(roi[:2]) < 0 or min(roi[2:]) < 1):
                raise ValueError("ROI must be [x, y, width, height], nonnegative integer origin, positive size")
        if self.reference_roi is not None and self.source_roi is None:
            raise ValueError("Explicit reference ROI requires an explicit source ROI")


def prepare(source_raw, source_mask, reference_raw, reference_mask, source_roi, reference_roi,
            source_gsd, reference_gsd, config, coarse=None):
    source = normalize(source_raw, source_mask, config.clahe)
    reference = normalize(reference_raw, reference_mask, config.clahe)
    rh, rw = reference.shape
    ratio = source_gsd / reference_gsd
    if ratio <= 0:
        raise ValueError("Ground sample distances must be positive")
    # One common physical-resolution factor, never force unrelated widths to agree.
    extent = max(rw, rh) if coarse is not None else max(rw, rh, source.shape[1]*ratio, source.shape[0]*ratio)
    common_scale = min(1., config.max_size / extent)
    tw, th = max(8, round(rw * common_scale)), max(8, round(rh * common_scale))
    ref_resize = resize_matrix(rw, rh, tw, th)
    ref_image = cv2.resize(reference, (tw, th), interpolation=cv2.INTER_AREA)
    ref_mask = cv2.resize(reference_mask, (tw, th), interpolation=cv2.INTER_NEAREST)
    target_transform = ref_resize @ translation(-reference_roi[0], -reference_roi[1])
    if coarse is not None:
        source_transform = target_transform @ coarse
        # Area downsample before geometric warping to avoid severe aliasing.
        downscale = min(1., float(np.linalg.svd(source_transform[:2, :2], compute_uv=False).max()))
    else:
        downscale = min(1., ratio * common_scale)
    sh, sw = source.shape
    dw, dh = max(8, round(sw * downscale)), max(8, round(sh * downscale))
    if min(dw, dh) < 32:
        raise ValueError("OHRC region is too small at TMC-2 resolution; assemble a larger source ROI")
    small = cv2.resize(source, (dw, dh), interpolation=cv2.INTER_AREA)
    # Area-resampling mask rejects pixels contaminated by invalid input samples.
    small_mask = (cv2.resize(source_mask, (dw, dh), interpolation=cv2.INTER_AREA) >= 254).astype(np.uint8) * 255
    down = resize_matrix(sw, sh, dw, dh)
    if coarse is not None:
        local = source_transform @ translation(source_roi[0], source_roi[1]) @ np.linalg.inv(down)
        source_image = cv2.warpPerspective(small, local, (tw, th), flags=cv2.INTER_LINEAR)
        src_mask = cv2.warpPerspective(small_mask, local, (tw, th), flags=cv2.INTER_NEAREST)
    else:
        source_image, src_mask = small, small_mask
        source_transform = down @ translation(-source_roi[0], -source_roi[1])
    src_mask = cv2.erode(src_mask, np.ones((5, 5), np.uint8))
    ref_mask = cv2.erode(ref_mask, np.ones((5, 5), np.uint8))
    if min(np.count_nonzero(src_mask), np.count_nonzero(ref_mask)) < 1024:
        raise ValueError("Too little valid area after coarse alignment")
    source_image[src_mask == 0] = 0
    ref_image[ref_mask == 0] = 0
    return source_image, src_mask, ref_image, ref_mask, source_transform, target_transform, ref_resize, reference


def run(config: RunConfig, matcher=None, store=None, run_id=None):
    start = time.monotonic()
    run_id = run_id or uuid.uuid4().hex
    if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
        raise ValueError("run_id must be 32 lowercase hex characters")
    output = Path(config.output_root) / run_id
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema_version": "1.0", "run_id": run_id, "pair_id": config.pair_id,
              "status": "FAILED", "method": "pretrained_loftr_outdoor", "scope": "local_ROI",
              "reason": None, "metrics": {}, "correspondences": [], "transformation": None,
              "validation": {"independent_checkpoint_rmse_tmc2_px": None,
                             "subpixel_accuracy_verified": False,
                             "type": "inlier_fit_only", "note": "Fitting error is not independent registration accuracy"},
              "config": asdict(config), "artifacts": {}}
    try:
        store = store or TileStore(config.repo_id, config.revision, config.cache_dir, config.local_root, config.offline)
        pair = store.pair(config.pair_id)
        source_pid = pair.get("source_product_id") or pair["ohrc_product_id"]
        ref_pid = pair.get("reference_product_id") or pair["tmc2_product_id"]
        source_product = store.products[source_pid]
        ref_product = store.products[ref_pid]
        source_gsd = float(source_product["pixel_resolution_m"])
        ref_gsd = float(ref_product["pixel_resolution_m"])
        source_roi = config.source_roi or centered_roi(source_product["width"], source_product["height"], config.source_side)
        coarse = None
        result["provenance"] = {"tile_repo": store.repo_id, "tile_revision": store.revision,
                                "local_root": config.local_root, "pair": pair}
        if config.reference_roi is None:
            if source_pid == ref_pid:
                x, y, w, h = source_roi
                off = w // 4
                reference_roi = [
                    min(x + off, ref_product["width"] - w),
                    min(y + off, ref_product["height"] - h),
                    w, h,
                ]
                result["coarse_alignment"] = {"method": "same_product_offset", "is_ground_truth": False}
            else:
                LOG.info("Locating overlap using source geolocation grids")
                paths = [fetch_grid(p, store, config.geometry_repo, config.geometry_revision) for p in (source_product, ref_product)]
                reference_roi, coarse, geo_error = locate_reference(source_roi, GeoGrid(paths[0][0]), GeoGrid(paths[1][0]),
                                                                     ref_product, config.reference_margin)
                result["coarse_alignment"] = {"method": "local_geolocation_affine", "geometry_sources": [p[1] for p in paths],
                                               "fit_rmse_tmc2_px": geo_error, "matrix_full_ohrc_to_full_tmc2": coarse.tolist(),
                                               "is_ground_truth": False}
        else:
            reference_roi = config.reference_roi
            result["coarse_alignment"] = {"method": "user_ROIs_and_GSD", "is_ground_truth": False}
        result["regions"] = {"source_roi_xywh": source_roi, "reference_roi_xywh": reference_roi,
                             "source_gsd_m": source_gsd, "reference_gsd_m": ref_gsd}
        a, ma = store.assemble(source_pid, source_roi, config.workers)
        b, mb = store.assemble(ref_pid, reference_roi, config.workers)
        sa, sm, rb, rm, ts, tr, rr, ref_native = prepare(a, ma, b, mb, source_roi, reference_roi,
                                                        source_gsd, ref_gsd, config, coarse)
        del a, ma, b, mb
        result["working"] = {"source_shape_hw": list(sa.shape), "reference_shape_hw": list(rb.shape),
                              "full_source_to_working": ts.tolist(), "full_reference_to_working": tr.tolist()}
        matcher = matcher or LoFTRMatcher(config.device, config.checkpoint, config.threads)
        LOG.info("LoFTR inference on %s: source %s, reference %s", matcher.device, sa.shape, rb.shape)
        p0, p1, scores = matcher(sa, rb, sm, rm)
        result["provenance"].update({"device": matcher.device, "checkpoint_sha256": matcher.checkpoint_sha256})
        result["metrics"]["raw_match_count"] = len(p0)
        p0, p1, scores = filter_matches(p0, p1, scores, sm, rm, config.min_confidence)
        native_target = transform_points(np.linalg.inv(rr), p1)
        matrix, inliers, reason = estimate(p0, native_target, config.model, config.ransac_threshold)
        result["metrics"].update({"filtered_matches": len(p0), "inliers": int(inliers.sum()),
                                   "inlier_ratio": float(inliers.mean()) if len(inliers) else 0.,
                                   "mean_match_confidence": float(scores.mean()) if len(scores) else None,
                                   "confidence_is_calibrated_probability": False})
        errors = [None] * len(p0)
        registered = overlap = None
        if matrix is not None:
            try:
                # Reject horizons/folds at the input frame boundary.
                sh, sw = sa.shape
                corners = np.array([[0, 0], [sw-1, 0], [sw-1, sh-1], [0, sh-1]], np.float64)
                denom = np.c_[corners, np.ones(4)] @ matrix[2]
                projected = transform_points(matrix, corners)
                if not (np.all(denom > 1e-8) or np.all(denom < -1e-8)) or not cv2.isContourConvex(projected.astype(np.float32)):
                    raise ValueError("Transformation folds or crosses a projective horizon")
                errors, metrics = residual_metrics(matrix, p0, native_target, inliers)
                result["metrics"].update(metrics)
                hwork = rr @ matrix
                singular = np.linalg.svd(hwork[:2, :2], compute_uv=False)
                plausible = bool(singular.min() > .25 and singular.max() < 4)
                src_area = int(np.count_nonzero(sm))
                src_cov = hull_coverage(p0[inliers], src_area)
                ref_cov = hull_coverage(p1[inliers], int(np.count_nonzero(rm)))
                registered = cv2.warpPerspective(sa, hwork, (rb.shape[1], rb.shape[0]))
                warped_mask = cv2.warpPerspective(sm, hwork, (rb.shape[1], rb.shape[0]), flags=cv2.INTER_NEAREST)
                overlap = cv2.bitwise_and(warped_mask, rm)
                overlap_fraction = np.count_nonzero(overlap) / max(1, np.count_nonzero(rm))
                result["metrics"].update({"source_hull_coverage": src_cov, "reference_hull_coverage": ref_cov,
                                          "valid_overlap_fraction_of_reference": float(overlap_fraction),
                                          "residual_scale_plausible": plausible,
                                          "subpixel_inlier_fit": metrics["inlier_rmse_tmc2_px"] < 1})
                accepted = (inliers.sum() >= 20 and inliers.mean() >= .2 and src_cov >= .05
                            and ref_cov >= .02 and overlap_fraction >= .02 and plausible
                            and metrics["inlier_rmse_tmc2_px"] <= config.ransac_threshold)
                result["status"] = "REGISTERED_UNVERIFIED" if accepted else "LOW_CONFIDENCE"
                result["reason"] = None if accepted else "Candidate failed one or more heuristic count, coverage, overlap, or geometry gates"
                result["confidence"] = {"label": "candidate_supported" if accepted else "low",
                                         "basis": "heuristic geometric support; not an accuracy certificate"}
                full = translation(reference_roi[0], reference_roi[1]) @ matrix @ ts
                result["transformation"] = {"model": config.model, "direction": "OHRC_to_TMC2",
                                             "coordinate_convention": "zero-based pixel centers; x=column, y=row",
                                             "full_native_matrix": (full / full[2, 2]).tolist(),
                                             "source_working_to_reference_working": hwork.tolist(),
                                             "source_working_to_reference_native_roi": matrix.tolist()}
                native_registered = cv2.warpPerspective(sa, matrix, (reference_roi[2], reference_roi[3]))
                write_image(output / "registered_tmc2_native_roi.png", native_registered)
                write_image(output / "reference_tmc2_native_roi.png", ref_native)
                native_mask = cv2.warpPerspective(sm, matrix, (reference_roi[2], reference_roi[3]), flags=cv2.INTER_NEAREST)
                write_image(output / "registered_tmc2_native_mask.png", native_mask)
            except ValueError as exc:
                reason = str(exc)
                matrix = None
                inliers[:] = False
                registered = overlap = None
        if matrix is None:
            result["reason"] = reason
            result["metrics"]["inliers"] = 0
            result["metrics"]["inlier_ratio"] = 0.
        raw_source = transform_points(np.linalg.inv(ts), p0)
        raw_reference = transform_points(np.linalg.inv(tr), p1)
        result["correspondences"] = [{"ohrc_x": float(s[0]), "ohrc_y": float(s[1]),
                                       "tmc2_x": float(t[0]), "tmc2_y": float(t[1]),
                                       "match_confidence": float(c), "inlier": bool(i),
                                       "error_tmc2_px": float(e) if e is not None else None}
                                      for s, t, c, i, e in zip(raw_source, raw_reference, scores, inliers, errors)]
        result["elapsed_seconds"] = round(time.monotonic() - start, 3)
        write_artifacts(output, result, sa, rb, p0, p1, scores, inliers, registered, overlap)
        if matrix is not None:
            result["artifacts"].update({"registered_native_roi": "registered_tmc2_native_roi.png",
                                        "reference_native_roi": "reference_tmc2_native_roi.png",
                                        "registered_native_mask": "registered_tmc2_native_mask.png"})
        (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        LOG.info("%s: %s; output %s", config.pair_id, result["status"], output)
    except Exception as exc:
        LOG.exception("Registration failed")
        result.update(status="FAILED", reason=f"{type(exc).__name__}: {exc}", elapsed_seconds=round(time.monotonic()-start, 3))
        result["artifacts"]["result"] = "result.json"
        (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return result
