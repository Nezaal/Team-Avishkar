from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys, os, json, cv2, time, uuid
import numpy as np
import torch
from pathlib import Path
import logging

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from lightglue import LightGlue, SuperPoint, utils
from loftr_pipeline.data import TileStore, centered_roi
from loftr_pipeline.pipeline import prepare, RunConfig
from loftr_pipeline.matching import filter_matches, estimate, residual_metrics
from loftr_pipeline.artifacts import write_artifacts
from loftr_pipeline.matching import LoFTRMatcher

app = FastAPI(title="ChandraMatch CV API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegistrationRequest(BaseModel):
    pair_id: str
    algorithm: str = "SIFT"
    device: str = "cuda"

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

def run_loftr(sa, rb, sm, rm, matcher):
    p0, p1, scores = matcher(sa, rb, sm, rm)
    return p0, p1, scores, 0

def run_lightglue(sa, rb, sm, rm, lg_matcher, sp_extractor, device):
    def prep_tensor(x):
        return torch.from_numpy(x).float().unsqueeze(0).unsqueeze(0).to(device) / 255.0
    img0 = prep_tensor(sa)
    img1 = prep_tensor(rb)
    with torch.inference_mode():
        feats0 = sp_extractor.extract(img0)
        feats1 = sp_extractor.extract(img1)
        matches01 = lg_matcher({"image0": feats0, "image1": feats1})
    feats0, feats1, matches01 = [utils.rbd(x) for x in [feats0, feats1, matches01]]
    kpts0, kpts1, matches = feats0["keypoints"], feats1["keypoints"], matches01["matches"]
    m_kpts0, m_kpts1 = kpts0[matches[..., 0]], kpts1[matches[..., 1]]
    p0 = m_kpts0.cpu().numpy()
    p1 = m_kpts1.cpu().numpy()
    scores = matches01["scores"].cpu().numpy()
    return p0, p1, scores, len(kpts0)

@app.get("/pairs")
def get_pairs():
    return {"pairs": [
        {"pair_id": "pair_020", "region": "OHRC Baseline", "ohrc_resolution_m": 0.25, "tmc2_resolution_m": 0.25, "resolution_ratio": 1.0, "ohrc_product_id": "ch2_ohr_ncp_20200825T1322594314_d_img_d18", "tmc2_product_id": "ch2_ohr_ncp_20200825T1716291272_d_img_d18"}
    ]}

@app.post("/register")
def register(request: RegistrationRequest):
    run_id = uuid.uuid4().hex
    out_dir = Path(ROOT_DIR) / "baseline_outputs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    store = TileStore(local_root=ROOT_DIR, cache_dir="C:/hfcache", offline=True)
    pair = store.pair(request.pair_id)
    config = RunConfig(pair_id=request.pair_id, max_size=1024, local_root=".", ransac_threshold=3.0)
    
    source_roi = centered_roi(12000, 90148, 8192)
    reference_roi = centered_roi(12000, 93693, 8192)
    
    src_id = pair.get("source_product_id") or pair.get("ohrc_product_id")
    ref_id = pair.get("reference_product_id") or pair.get("tmc2_product_id")
    
    a, ma = store.assemble(src_id, source_roi, 6)
    b, mb = store.assemble(ref_id, reference_roi, 6)
    
    sa, sm, rb, rm, ts, tr, rr, native_target = prepare(a, ma, b, mb, source_roi, reference_roi, 0.25, 0.25, config)
    
    method = request.algorithm
    
    if method == "SIFT":
        p0, p1, scores, detected = run_sift(sa, rb, sm, rm)
    elif method == "LoFTR":
        matcher = LoFTRMatcher(device=request.device)
        p0, p1, scores, detected = run_loftr(sa, rb, sm, rm, matcher)
    else: # LightGlue
        extractor = SuperPoint(max_num_keypoints=4096).eval().to(request.device)
        lg = LightGlue(features='superpoint').eval().to(request.device)
        p0, p1, scores, detected = run_lightglue(sa, rb, sm, rm, lg, extractor, request.device)

    p0, p1, scores = filter_matches(p0, p1, scores, sm, rm, 0.1)
    
    # Map p1 to native coordinates of reference image
    native_target = np.c_[p1, np.ones(len(p1))] @ np.linalg.inv(rr).T
    native_target = native_target[:, :2] / native_target[:, 2:]
    
    matrix, inliers, reason = estimate(p0, native_target, model="affine", threshold=3.0)
    inliers_count = int(inliers.sum()) if inliers is not None else 0
    
    metrics = {
        "detected_features": detected,
        "raw_matches": len(p0) + (len(p0) if method != "LoFTR" else 0),
        "filtered_matches": len(p0),
        "RANSAC_inliers": inliers_count,
        "inlier_ratio": inliers_count / len(p0) if len(p0) > 0 else 0,
        "matcher_confidence": float(np.median(scores)) if len(scores) > 0 else 0.0
    }
    
    if matrix is not None and inliers_count > 0:
        errs, metrics_resid = residual_metrics(matrix, p0, native_target, inliers)
        metrics["reprojection_RMSE"] = metrics_resid.get("inlier_rmse_tmc2_px", None)
        metrics["median_residual"] = metrics_resid.get("inlier_median_tmc2_px", None)
        
        hwork = rr @ matrix
        registered = cv2.warpPerspective(sa, hwork, (rb.shape[1], rb.shape[0]))
        warped_mask = cv2.warpPerspective(sm, hwork, (rb.shape[1], rb.shape[0]), flags=cv2.INTER_NEAREST)
        overlap = cv2.bitwise_and(warped_mask, rm)
        
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
            
        result_dict = {"correspondences": corrs, "pair_id": request.pair_id, "status": "SUCCESS", "transformation": {"model": "affine"}}
        write_artifacts(out_dir, result_dict, sa, rb, p0, p1, scores, inliers, registered, overlap)
        artifacts = result_dict.get("artifacts", {})
        
        # Downscale images for web viewing (browser memory limit)
        for name, path_str in artifacts.items():
            if name in ["source", "reference", "overlay", "checkerboard", "matches"]:
                img_path = out_dir / path_str
                if img_path.exists():
                    img = cv2.imread(str(img_path))
                    if img is not None and max(img.shape[:2]) > 2048:
                        scale = 2048 / max(img.shape[:2])
                        small = cv2.resize(img, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                        cv2.imwrite(str(img_path), small)
    else:
        artifacts = {}
        corrs = []
        
    result = {
        "run_id": run_id,
        "pair_id": request.pair_id,
        "status": "SUCCESS" if inliers_count > 10 else "FAILED",
        "correspondences": corrs,
        "artifacts": artifacts,
        "metrics": metrics,
        "reprojectionError": {
            "mean": metrics.get("reprojection_RMSE"),
            "median": metrics.get("median_residual")
        },
        "correspondence": {
            "totalPoints": metrics["detected_features"],
            "filteredPoints": metrics["filtered_matches"],
            "inlierCount": metrics["RANSAC_inliers"],
            "inlierPct": round(metrics["inlier_ratio"] * 100)
        }
    }
    
    with open(out_dir / "result.json", "w") as f:
        json.dump(result, f)
        
    return result

@app.get("/runs/{run_id}/artifacts/{name}")
def get_artifact(run_id: str, name: str):
    path = Path(ROOT_DIR) / "baseline_outputs" / run_id / name
    if not path.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(path)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
