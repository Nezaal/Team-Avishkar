import time
import uuid
import json
import logging
from pathlib import Path

import cv2
import numpy as np
import torch
from lightglue import LightGlue, SuperPoint, utils

from loftr_pipeline.data import TileStore, centered_roi
from loftr_pipeline.pipeline import prepare, RunConfig
from loftr_pipeline.matching import filter_matches, estimate, residual_metrics, hull_coverage
from loftr_pipeline.artifacts import write_artifacts

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def run_lightglue(config: RunConfig):
    start = time.monotonic()
    
    # Setup unique output directory
    run_id = "lg_" + uuid.uuid4().hex[:29]
    output_dir = Path(config.output_root) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize basic result dictionary
    result = {
        "run_id": run_id,
        "pair_id": config.pair_id,
        "method": "superpoint_lightglue",
        "status": "FAILED",
        "reason": None,
        "metrics": {},
        "artifacts": {}
    }
    
    try:
        # 1. Load Data
        store = TileStore(local_root=".", cache_dir="C:/hfcache")
        pair = store.pair(config.pair_id)
        
        source_roi = centered_roi(12000, 93693, 8192)
        reference_roi = [1416, 220871, 744, 714]
        
        logging.info("Loading tiles...")
        a, ma = store.assemble(pair["ohrc_product_id"], source_roi, 6)
        b, mb = store.assemble(pair["tmc2_product_id"], reference_roi, 6)
        
        # 2. Prepare
        sa, sm, rb, rm, ts, tr, rr, ref_native = prepare(a, ma, b, mb, source_roi, reference_roi, 0.25, 4.48, config, coarse=None)
        
        # 3. SuperPoint + LightGlue
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        extractor = SuperPoint(max_num_keypoints=2048).eval().to(device)
        matcher = LightGlue(features='superpoint').eval().to(device)
        
        img0 = torch.from_numpy(sa).float()[None, None].to(device) / 255.0
        img1 = torch.from_numpy(rb).float()[None, None].to(device) / 255.0
        
        logging.info("Running neural network...")
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
        
        # 4. Filter & Estimate
        p0, p1, scores = filter_matches(p0, p1, scores, sm, rm, threshold=config.min_confidence)
        result["metrics"]["filtered_matches"] = len(p0)
        
        native_target = np.c_[p1, np.ones(len(p1))] @ np.linalg.inv(rr).T
        native_target = native_target[:, :2] / native_target[:, 2:]
        
        matrix, inliers, reason = estimate(p0, native_target, config.model, config.ransac_threshold)
        
        if matrix is not None:
            result["status"] = "REGISTERED_UNVERIFIED"
            result["metrics"]["inliers"] = int(inliers.sum())
            result["metrics"]["inlier_ratio"] = float(inliers.mean())
            # For this quick test, we skip drawing the fully registered wrap (sets it to None)
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

        # 5. Write Visual Artifacts!
        logging.info("Saving visual artifacts...")
        write_artifacts(output_dir, result, sa, rb, p0, p1, scores, inliers)
        
        result["artifacts"]["result"] = "result.json"
        with open(output_dir / "result.json", "w") as f:
            json.dump(result, f, indent=2)
            
        logging.info(f"DONE! Artifacts saved to: {output_dir}")
        
    except Exception as e:
        logging.error(f"Failed: {e}")

if __name__ == '__main__':
    run_lightglue(RunConfig(pair_id="pair_001", max_size=512, local_root=".", ransac_threshold=5.0))
