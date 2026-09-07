import time
import uuid
import json
import logging
from pathlib import Path
from dataclasses import asdict

import cv2
import numpy as np
import torch
from lightglue import LightGlue, SuperPoint, utils

from loftr_pipeline.data import TileStore, centered_roi
from loftr_pipeline.pipeline import prepare, RunConfig
from loftr_pipeline.matching import filter_matches, estimate
from loftr_pipeline.artifacts import write_artifacts

LOG = logging.getLogger(__name__)

def run_lightglue(config: RunConfig, store=None, run_id=None):
    start = time.monotonic()
    
    run_id = run_id or ("lg_" + uuid.uuid4().hex[:29])
    output_dir = Path(config.output_root) / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    
    result = {
        "schema_version": "1.0",
        "run_id": run_id, 
        "pair_id": config.pair_id,
        "method": "superpoint_lightglue",
        "scope": "local_ROI",
        "status": "FAILED",
        "reason": None,
        "metrics": {},
        "config": asdict(config),
        "artifacts": {}
    }
    
    try:
        store = store or TileStore(local_root=config.local_root, cache_dir=config.cache_dir, offline=config.offline)
        pair = store.pair(config.pair_id)

        source_pid = pair.get("source_product_id") or pair["ohrc_product_id"]
        ref_pid = pair.get("reference_product_id") or pair["tmc2_product_id"]
        source_product = store.products[source_pid]
        ref_product = store.products[ref_pid]
        source_gsd = float(source_product["pixel_resolution_m"])
        ref_gsd = float(ref_product["pixel_resolution_m"])

        source_roi = config.source_roi or centered_roi(source_product["width"], source_product["height"], config.source_side)
        reference_roi = config.reference_roi

        if reference_roi is None:
            if source_pid == ref_pid:
                x, y, w, h = source_roi
                off = w // 4
                reference_roi = [
                    min(x + off, ref_product["width"] - w),
                    min(y + off, ref_product["height"] - h),
                    w, h,
                ]
            elif config.pair_id == "pair_001":
                reference_roi = [1416, 220871, 744, 714]
            else:
                raise ValueError("Explicit reference_roi is required when geometry repo is unavailable.")

        LOG.info("Assembling source and reference tiles...")
        a, ma = store.assemble(source_pid, source_roi, config.workers)
        b, mb = store.assemble(ref_pid, reference_roi, config.workers)

        sa, sm, rb, rm, ts, tr, rr, ref_native = prepare(a, ma, b, mb, source_roi, reference_roi, source_gsd, ref_gsd, config, coarse=None)
        
        device = torch.device('cuda' if (config.device in ("auto", "cuda") and torch.cuda.is_available()) else 'cpu')
        LOG.info(f"SuperPoint+LightGlue inference on {device}: source {sa.shape}, reference {rb.shape}")
        
        extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)
        matcher = LightGlue(features='superpoint').eval().to(device)
        
        img0 = torch.from_numpy(sa).float()[None, None].to(device) / 255.0
        img1 = torch.from_numpy(rb).float()[None, None].to(device) / 255.0
        
        with torch.inference_mode():
            feats0 = extractor.extract(img0)
            feats1 = extractor.extract(img1)
            matches01 = matcher({'image0': feats0, 'image1': feats1})
        
        feats0, feats1, matches01 = [utils.rbd(x) for x in [feats0, feats1, matches01]]
        kpts0, kpts1, matches = feats0['keypoints'], feats1['keypoints'], matches01['matches']
        
        if len(matches) == 0:
            raise ValueError("0 tentative matches found by LightGlue")
            
        p0 = kpts0[matches[..., 0]].cpu().numpy()
        p1 = kpts1[matches[..., 1]].cpu().numpy()
        scores = matches01['scores'].cpu().numpy()
        
        result["metrics"]["raw_match_count"] = len(p0)
        
        p0, p1, scores = filter_matches(p0, p1, scores, sm, rm, threshold=config.min_confidence)
        result["metrics"]["filtered_matches"] = len(p0)
        
        native_target = np.c_[p1, np.ones(len(p1))] @ np.linalg.inv(rr).T
        native_target = native_target[:, :2] / native_target[:, 2:]
        
        matrix, inliers, reason = estimate(p0, native_target, config.model, config.ransac_threshold)
        
        if matrix is not None:
            result["status"] = "REGISTERED_UNVERIFIED"
            result["metrics"]["inliers"] = int(inliers.sum())
            result["metrics"]["inlier_ratio"] = float(inliers.mean())
        else:
            result["reason"] = reason
            result["metrics"]["inliers"] = 0
            inliers = np.zeros(len(p0), dtype=bool)

        from loftr_pipeline.geometry import transform_points
        raw_source = transform_points(np.linalg.inv(ts), p0)
        raw_reference = transform_points(np.linalg.inv(tr), p1)
        result["correspondences"] = [{"ohrc_x": float(s[0]), "ohrc_y": float(s[1]),
                                      "tmc2_x": float(t[0]), "tmc2_y": float(t[1]),
                                      "match_confidence": float(c), "inlier": bool(i),
                                      "error_tmc2_px": None}
                                     for s, t, c, i in zip(raw_source, raw_reference, scores, inliers)]

        LOG.info("Saving visual artifacts...")
        write_artifacts(output_dir, result, sa, rb, p0, p1, scores, inliers)
        
        result["elapsed_seconds"] = round(time.monotonic() - start, 3)
        result["artifacts"]["result"] = "result.json"
        
        with open(output_dir / "result.json", "w") as f:
            json.dump(result, f, indent=2)
            
    except Exception as exc:
        LOG.exception("Registration failed")
        result.update(status="FAILED", reason=f"{type(exc).__name__}: {exc}", elapsed_seconds=round(time.monotonic()-start, 3))
        result["artifacts"]["result"] = "result.json"
        with open(output_dir / "result.json", "w") as f:
            json.dump(result, f, indent=2)
            
    return result
