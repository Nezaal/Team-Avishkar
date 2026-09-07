from .extractor import extract_features
from .matcher import match_features
from .homography import compute_homography
from .metrics import calculate_rmse, map_to_raw_coordinates

def register_images(source_prep, reference_prep, pair_meta):
    # 1. Extract metadata
    scale_x1, scale_y1 = source_prep["scale_x"], source_prep["scale_y"]
    scale_x2, scale_y2 = reference_prep["scale_x"], reference_prep["scale_y"]
    tmc2_y_offset = (int(pair_meta["tmc2_height"]) - reference_prep["original_height"]) // 2

    # 2. Extract Features
    kp1, des1 = extract_features(source_prep["image"], source_prep["mask"])
    kp2, des2 = extract_features(reference_prep["image"], reference_prep["mask"])

    # 3. Match Features
    all_matches, good_matches, src_pts, dst_pts = match_features(kp1, des1, kp2, des2)
    if src_pts is None:
        return {"status": "FAILED", "reason": "Insufficient keypoints or matches"}

    # 4. Homography Matrix
    H, mask = compute_homography(src_pts, dst_pts)
    if H is None or mask is None:
        return {"status": "FAILED", "reason": "Homography failed"}
    
    inliers = sum(mask.ravel().tolist())
    if inliers < 4:
        return {"status": "FAILED", "reason": "Not enough RANSAC inliers"}

    # 5. Metrics & Coordinate Mapping
    rmse = calculate_rmse(src_pts, dst_pts, mask, H)
    correspondences = map_to_raw_coordinates(
        src_pts, dst_pts, mask, 
        scale_x1, scale_y1, scale_x2, scale_y2, tmc2_y_offset
    )

    confidence = "SUCCESS (High Confidence)" if (inliers > 15 and rmse < 1.0) else "LOW_CONFIDENCE"

    return {
        "status": confidence,
        "metrics": {
            "rmse_pixel_error": round(rmse, 4),
            "inliers": inliers,
            "tentative_matches": len(all_matches)
        },
        "transformation_matrix": H.tolist(),
        "correspondences": correspondences
    }
