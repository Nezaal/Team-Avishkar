"""
Verification test suite for Module B7 RansacEstimator (backend/tests/test_b7_ransac.py).
Covers Tests 1 to 8 as specified in STEP 53 requirements.
"""
import sys
import os
import numpy as np
import cv2

ROOT = r"C:\Users\Umang Kadian\Desktop\Team-Avishkar"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_1_import():
    print("=== TEST 1: IMPORT TEST ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator()
    assert estimator is not None
    print("Import test passed.")

def test_2_synthetic_homography():
    print("\n=== TEST 2: SYNTHETIC HOMOGRAPHY ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator(reprojection_threshold=3.0)

    np.random.seed(42)
    # Generate 50 non-collinear points
    src_pts = np.random.uniform(10, 500, (50, 2)).astype(np.float32)

    # Known translation + scale transformation (Homography 3x3)
    H_true = np.array([[1.1, 0.05, 12.0], [-0.02, 1.05, 8.0], [0.0001, -0.0001, 1.0]], dtype=np.float32)

    # Transform src_pts to dst_pts
    src_homo = np.hstack([src_pts, np.ones((50, 1), dtype=np.float32)])
    dst_homo = (H_true @ src_homo.T).T
    dst_pts = (dst_homo[:, :2] / dst_homo[:, 2:3]).astype(np.float32)

    res = estimator.estimate_from_points(src_pts, dst_pts, tile_a_id="synthetic_a", tile_b_id="synthetic_b")
    print(f"Status: {res['status']}, Inliers: {res['inlier_count']}/{res['input_matches_count']}")
    assert res["status"] == "SUCCESS", f"Expected SUCCESS, got {res['status']}"
    assert res["homography"] is not None and res["homography"].shape == (3, 3), "Homography shape mismatch"
    assert res["inlier_count"] >= 45, f"Expected high inlier count, got {res['inlier_count']}"
    print("Synthetic homography test passed.")

def test_3_outlier_rejection():
    print("\n=== TEST 3: OUTLIER REJECTION ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator(reprojection_threshold=3.0)

    np.random.seed(42)
    # 40 clean matches + 10 bad outliers
    src_pts = np.random.uniform(10, 500, (50, 2)).astype(np.float32)
    H_true = np.array([[1.0, 0.0, 20.0], [0.0, 1.0, -15.0], [0.0, 0.0, 1.0]], dtype=np.float32)

    src_homo = np.hstack([src_pts, np.ones((50, 1), dtype=np.float32)])
    dst_homo = (H_true @ src_homo.T).T
    dst_pts = (dst_homo[:, :2] / dst_homo[:, 2:3]).astype(np.float32)

    # Add 10 random noise outliers to dst_pts
    dst_pts[40:] += np.random.uniform(50, 200, (10, 2)).astype(np.float32)

    res = estimator.estimate_from_points(src_pts, dst_pts)
    print(f"Inliers: {res['inlier_count']}, Outliers: {res['outlier_count']}, Ratio: {res['inlier_ratio']:.3f}")
    assert res["status"] == "SUCCESS"
    assert res["outlier_count"] >= 8, f"Expected outliers to be detected, got {res['outlier_count']}"
    assert res["inlier_count"] >= 35, f"Expected clean matches to be retained, got {res['inlier_count']}"
    print("Outlier rejection test passed.")

def test_4_insufficient_matches():
    print("\n=== TEST 4: INSUFFICIENT MATCHES ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator(min_matches=4)

    src_pts = np.array([[10, 20], [30, 40], [50, 60]], dtype=np.float32) # Only 3 points
    dst_pts = np.array([[15, 25], [35, 45], [55, 65]], dtype=np.float32)

    res = estimator.estimate_from_points(src_pts, dst_pts)
    assert res["status"] == "INSUFFICIENT_MATCHES", f"Expected INSUFFICIENT_MATCHES, got {res['status']}"
    assert res["homography"] is None, "Homography should be None"
    assert res["inlier_count"] == 0
    print("Insufficient matches test passed.")

def test_5_empty_input():
    print("\n=== TEST 5: EMPTY INPUT ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator()

    src_empty = np.empty((0, 2), dtype=np.float32)
    dst_empty = np.empty((0, 2), dtype=np.float32)

    res = estimator.estimate_from_points(src_empty, dst_empty)
    assert res["status"] == "INSUFFICIENT_MATCHES"
    assert res["homography"] is None
    assert res["src_inliers"].shape == (0, 2)
    assert res["dst_inliers"].shape == (0, 2)
    print("Empty input test passed.")

def test_6_malformed_input():
    print("\n=== TEST 6: MALFORMED INPUT ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator()

    # 3D array
    res_3d = estimator.estimate_from_points(np.ones((10, 2, 2)), np.ones((10, 2, 2)))
    assert res_3d["status"] == "INVALID_INPUT", f"Expected INVALID_INPUT, got {res_3d['status']}"

    # Shape (N, 3)
    res_n3 = estimator.estimate_from_points(np.ones((10, 3)), np.ones((10, 3)))
    assert res_n3["status"] == "INVALID_INPUT"

    # Mismatched lengths
    res_len = estimator.estimate_from_points(np.ones((10, 2)), np.ones((8, 2)))
    assert res_len["status"] == "INVALID_INPUT"

    # None input
    res_none = estimator.estimate_from_points(None, np.ones((10, 2)))
    assert res_none["status"] == "INVALID_INPUT"

    print("Malformed input test passed.")

def test_7_inlier_coordinate_alignment():
    print("\n=== TEST 7: INLIER COORDINATE ALIGNMENT ===")
    from backend.pipeline.ransac import RansacEstimator
    estimator = RansacEstimator()

    np.random.seed(42)
    # Non-collinear 2D random points
    src_pts = np.random.uniform(10, 500, (30, 2)).astype(np.float32)
    dst_pts = src_pts + np.array([10.0, -5.0], dtype=np.float32)

    res = estimator.estimate_from_points(src_pts, dst_pts)
    mask = res["inlier_mask"]
    src_inliers = res["src_inliers"]
    dst_inliers = res["dst_inliers"]

    expected_src = src_pts[mask == 1]
    expected_dst = dst_pts[mask == 1]

    assert np.allclose(src_inliers, expected_src), "src_inliers coordinate alignment failed"
    assert np.allclose(dst_inliers, expected_dst), "dst_inliers coordinate alignment failed"
    print("Inlier coordinate alignment test passed.")

def test_8_b6_b7_integration():
    print("\n=== TEST 8: B6 -> B7 INTEGRATION ===")
    from backend.pipeline.matcher import FeatureMatcher
    from backend.pipeline.ransac import RansacEstimator

    matcher = FeatureMatcher(method="bf", ratio_threshold=0.85)
    estimator = RansacEstimator(reprojection_threshold=5.0)

    np.random.seed(42)
    # Distinct descriptors for 36 features
    desc_a = np.eye(36, 128, dtype=np.float32) * 10.0
    desc_b = desc_a.copy() # Exact match descriptors

    # Create 2D grid of non-collinear keypoint positions (6x6 grid)
    kps_a = [
        cv2.KeyPoint(x=float(10 + (i % 6) * 50), y=float(20 + (i // 6) * 50), size=1.0)
        for i in range(36)
    ]
    # Transform points by translation (+15, -20)
    kps_b = [
        cv2.KeyPoint(x=float(10 + (i % 6) * 50 + 15), y=float(20 + (i // 6) * 50 - 20), size=1.0)
        for i in range(36)
    ]

    match_res = matcher.match_descriptors(desc_a, desc_b, kps_a, kps_b, tile_a_id="tile_a", tile_b_id="tile_b")
    ransac_res = estimator.estimate(match_res)

    print(f"B6 Filtered Matches: {match_res['filtered_matches_count']}, B7 Inliers: {ransac_res['inlier_count']}")
    assert ransac_res["status"] == "SUCCESS", f"Expected SUCCESS, got {ransac_res['status']}"
    assert ransac_res["homography"] is not None and ransac_res["homography"].shape == (3, 3)
    assert ransac_res["inlier_count"] >= 30, f"Expected high inliers, got {ransac_res['inlier_count']}"
    print("B6 -> B7 integration test passed.")

def run_all():
    test_1_import()
    test_2_synthetic_homography()
    test_3_outlier_rejection()
    test_4_insufficient_matches()
    test_5_empty_input()
    test_6_malformed_input()
    test_7_inlier_coordinate_alignment()
    test_8_b6_b7_integration()
    print("\nALL STEP 53 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
