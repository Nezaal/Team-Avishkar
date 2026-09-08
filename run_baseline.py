import cv2
import numpy as np
import torch
import json
from pathlib import Path
import uuid
import time
import logging

from lightglue import LightGlue, SuperPoint, utils
from loftr_pipeline.data import TileStore, centered_roi
from loftr_pipeline.pipeline import prepare, RunConfig
from loftr_pipeline.matching import filter_matches, estimate, residual_metrics
from loftr_pipeline.artifacts import write_artifacts, write_image
from loftr_pipeline.matching import LoFTRMatcher

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def run_sift(sa, rb, sm, rm):
    sift = cv2.SIFT_create()
    k1, d1 = sift.detectAndCompute(sa, mask=sm)
    k2, d2 = sift.detectAndCompute(rb, mask=rm)
    if d1 is None or d2 is None or len(k1) == 0 or len(k2) == 0:
        return np.empty((0,2)), np.empty((0,2)), np.empty(0), 0
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(d1, d2, k=2)
    good = []
    scores = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)
            scores.append(1.0 - (m.distance / n.distance))
    p0 = np.float32([k1[m.queryIdx].pt for m in good])
    p1 = np.float32([k2[m.trainIdx].pt for m in good])
    return p0, p1, np.array(scores), len(k1) + len(k2)

def run_baseline():
    store = TileStore(local_root=".", cache_dir="C:/hfcache", offline=True)
    pair = store.pair("pair_020")
    config = RunConfig(pair_id="pair_020", max_size=1024, local_root=".", ransac_threshold=3.0)
    
    # Extract large ROI
    source_roi = centered_roi(12000, 90148, 8192)
    reference_roi = centered_roi(12000, 93693, 8192)
    
    logging.info("Loading tiles...")
    a, ma = store.assemble(pair["ohrc_product_id"], source_roi, 6)
    b, mb = store.assemble(pair["tmc2_product_id"], reference_roi, 6)
    
    # Because both are OHRC, their GSD is the same
    # from pairs.csv, ohrc_resolution_m=0.25, tmc2_resolution_m=0.25 for this pair
    gsd_a = 0.25
    gsd_b = 0.25
    
    logging.info("Preparing images...")
    sa, sm, rb, rm, ts, tr, rr, ref_native = prepare(a, ma, b, mb, source_roi, reference_roi, gsd_a, gsd_b, config)
    
    # Dictionary to store results for all 3 matchers
    results_all = {}
    methods = ["SIFT", "LoFTR", "LightGlue"]
    
    for method in methods:
        logging.info(f"--- Running {method} ---")
        run_id = f"baseline_{method.lower()}_{uuid.uuid4().hex[:8]}"
        out_dir = Path("baseline_outputs") / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        
        t0 = time.monotonic()
        
        detected_features = 0
        if method == "SIFT":
            p0, p1, scores, detected_features = run_sift(sa, rb, sm, rm)
        elif method == "LoFTR":
            matcher = LoFTRMatcher("cuda" if torch.cuda.is_available() else "cpu", None, 4)
            p0, p1, scores = matcher(sa, rb, sm, rm)
        elif method == "LightGlue":
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
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
            detected_features = len(kpts0) + len(kpts1)
            
            if len(matches) > 0:
                p0 = kpts0[matches[..., 0]].cpu().numpy()
                p1 = kpts1[matches[..., 1]].cpu().numpy()
                scores = matches01['scores'].cpu().numpy()
            else:
                p0, p1, scores = np.empty((0,2)), np.empty((0,2)), np.empty(0)
                
        raw_matches = len(p0)
        
        # Filter & Estimate
        if raw_matches > 0:
            if method != "SIFT":
                p0, p1, scores = filter_matches(p0, p1, scores, sm, rm, threshold=config.min_confidence)
            filtered_matches = len(p0)
            
            # Map p1 to native coordinates of reference image
            native_target = np.c_[p1, np.ones(len(p1))] @ np.linalg.inv(rr).T
            native_target = native_target[:, :2] / native_target[:, 2:]
            
            matrix, inliers, reason = estimate(p0, native_target, config.model, config.ransac_threshold)
        else:
            filtered_matches = 0
            matrix, inliers, reason = None, np.zeros(0, dtype=bool), "No raw matches"
            
        inliers_count = int(inliers.sum()) if inliers is not None else 0
        inlier_ratio = float(inliers.mean()) if inliers is not None and len(inliers) > 0 else 0.0
        
        metrics = {
            "detected_features": detected_features,
            "raw_matches": raw_matches,
            "filtered_matches": filtered_matches,
            "RANSAC_inliers": inliers_count,
            "inlier_ratio": inlier_ratio,
            "matcher_confidence": float(np.median(scores)) if len(scores) > 0 else 0.0
        }
        
        # If registered, compute residuals
        if matrix is not None and inliers_count > 0:
            errs, metrics_resid = residual_metrics(matrix, p0, native_target, inliers)
            metrics["reprojection_RMSE"] = metrics_resid.get("inlier_rmse_tmc2_px", None)
            metrics["median_residual"] = metrics_resid.get("inlier_median_error_tmc2_px", None)
            metrics["p90_residual"] = metrics_resid.get("inlier_p90_error_tmc2_px", None)
            
            # Save visual artifacts
            hwork = rr @ matrix
            registered = cv2.warpPerspective(sa, hwork, (rb.shape[1], rb.shape[0]))
            warped_mask = cv2.warpPerspective(sm, hwork, (rb.shape[1], rb.shape[0]), flags=cv2.INTER_NEAREST)
            overlap = cv2.bitwise_and(warped_mask, rm)
            
            # Construct correspondences for artifacts
            corrs = []
            for i in range(len(p0)):
                corrs.append({
                    "ohrc_x": float(p0[i][0]),
                    "ohrc_y": float(p0[i][1]),
                    "tmc2_x": float(p1[i][0]),
                    "tmc2_y": float(p1[i][1]),
                    "match_confidence": float(scores[i]),
                    "inlier": bool(inliers[i]),
                    "error_tmc2_px": float(errs[i]) if 'errs' in locals() and i < len(errs) else None
                })
            
            write_artifacts(out_dir, {"correspondences": corrs, "pair_id": "pair_020", "status": "SUCCESS"}, sa, rb, p0, p1, scores, inliers, registered, overlap)
            
            # Save full working transform matrix (Working -> Native Reference ROI)
            np.savetxt(out_dir / "transform_matrix.txt", matrix, fmt="%.6f")
            
        # Store results
        results_all[method] = {
            "metrics": metrics,
            "matrix": matrix.tolist() if matrix is not None else None
        }
        
        with open(out_dir / "results.json", "w") as f:
            json.dump(results_all[method], f, indent=2)
            
    print(json.dumps(results_all, indent=2))
        
if __name__ == '__main__':
    run_baseline()
