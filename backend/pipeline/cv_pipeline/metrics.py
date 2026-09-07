import cv2
import numpy as np

def calculate_rmse(src_pts, dst_pts, mask, H):
    inlier_src = src_pts[mask.ravel() == 1]
    inlier_dst = dst_pts[mask.ravel() == 1]
    
    inlier_src_proj = cv2.perspectiveTransform(inlier_src, H)
    errors = np.linalg.norm(inlier_src_proj - inlier_dst, axis=2)
    return float(np.sqrt(np.mean(errors**2)))

def map_to_raw_coordinates(src_pts, dst_pts, mask, scale_x1, scale_y1, scale_x2, scale_y2, tmc2_y_offset):
    matchesMask = mask.ravel().tolist()
    correspondences = []
    for i, is_inlier in enumerate(matchesMask):
        if is_inlier:
            w_x1, w_y1 = float(src_pts[i][0][0]), float(src_pts[i][0][1])
            w_x2, w_y2 = float(dst_pts[i][0][0]), float(dst_pts[i][0][1])
            
            correspondences.append({
                "ohrc_raw_x": round(w_x1 * scale_x1, 2), 
                "ohrc_raw_y": round(w_y1 * scale_y1, 2),
                "tmc2_raw_x": round(w_x2 * scale_x2, 2), 
                "tmc2_raw_y": round((w_y2 * scale_y2) + tmc2_y_offset, 2)
            })
    return correspondences
