"""
Verification test suite for Module B8 ImageRegistration (backend/tests/test_b8_registration.py).
Covers Tests 1 to 11 as specified in STEP 54 requirements.
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
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()
    assert reg is not None
    print("Import test passed.")

def test_2_identity_homography():
    print("\n=== TEST 2: IDENTITY HOMOGRAPHY ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    np.random.seed(42)
    img_a = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    img_b = img_a.copy()

    H_identity = np.eye(3, dtype=np.float64)
    b7_res = {"status": "SUCCESS", "homography": H_identity}

    res = reg.register(img_a, img_b, b7_res)
    print(f"Status: {res['status']}, MAE: {res['metrics']['mae']:.4f}")
    assert res["status"] == "SUCCESS"
    assert np.isclose(res["metrics"]["mae"], 0.0, atol=1e-5)
    assert np.isclose(res["metrics"]["mse"], 0.0, atol=1e-5)
    assert np.isclose(res["metrics"]["rmse"], 0.0, atol=1e-5)
    assert res["registered_image"].shape == img_a.shape
    print("Identity homography test passed.")

def test_3_known_translation():
    print("\n=== TEST 3: KNOWN TRANSLATION ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    # Synthetic image with a central box pattern
    img_a = np.zeros((200, 200), dtype=np.uint8)
    img_a[50:150, 50:150] = 200

    # Translate moving image by (+10, -5)
    H_trans = np.array([[1.0, 0.0, 10.0], [0.0, 1.0, -5.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    img_b = cv2.warpPerspective(img_a, H_trans, (200, 200))

    b7_res = {"status": "SUCCESS", "homography": H_trans}
    res = reg.register(img_a, img_b, b7_res)

    print(f"Status: {res['status']}, MAE: {res['metrics']['mae']:.4f}")
    assert res["status"] == "SUCCESS"
    assert res["registered_image"].shape == (200, 200)
    print("Known translation test passed.")

def test_4_invalid_homography():
    print("\n=== TEST 4: INVALID HOMOGRAPHY ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img = np.zeros((100, 100), dtype=np.uint8)

    # None homography
    res_none = reg.register(img, img, {"status": "SUCCESS", "homography": None})
    assert res_none["status"] == "INVALID_HOMOGRAPHY"

    # Wrong shape (2x2)
    res_shape = reg.register(img, img, {"status": "SUCCESS", "homography": np.eye(2)})
    assert res_shape["status"] == "INVALID_HOMOGRAPHY"

    # NaN in homography
    H_nan = np.eye(3)
    H_nan[0, 0] = np.nan
    res_nan = reg.register(img, img, {"status": "SUCCESS", "homography": H_nan})
    assert res_nan["status"] == "INVALID_HOMOGRAPHY"

    print("Invalid homography test passed.")

def test_5_b7_failure_safety():
    print("\n=== TEST 5: B7 FAILURE SAFETY ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img = np.zeros((100, 100), dtype=np.uint8)
    b7_fail = {"status": "INSUFFICIENT_MATCHES", "homography": None}

    res = reg.register(img, img, b7_fail)
    assert res["status"] == "INVALID_HOMOGRAPHY"
    assert res["registered_image"] is None
    print("B7 failure safety test passed.")

def test_6_mask_warping():
    print("\n=== TEST 6: MASK WARPING ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img_a = np.ones((100, 100), dtype=np.uint8) * 128
    img_b = img_a.copy()
    mask_b = np.full((100, 100), 255, dtype=np.uint8)
    mask_b[0:20, :] = 0 # Top 20 rows invalid

    H_identity = np.eye(3)
    b7_res = {"status": "SUCCESS", "homography": H_identity}

    res = reg.register(img_a, img_b, b7_res, mask_b=mask_b)
    reg_mask = res["registered_mask"]

    assert reg_mask is not None
    # Verify strict uint8 binary values (0 or 255)
    unique_vals = set(np.unique(reg_mask))
    assert unique_vals.issubset({0, 255}), f"Mask contains non-binary values: {unique_vals}"
    print("Mask warping test passed.")

def test_7_valid_region_metrics():
    print("\n=== TEST 7: VALID REGION METRICS ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img_a = np.ones((100, 100), dtype=np.uint8) * 100
    img_b = np.ones((100, 100), dtype=np.uint8) * 200 # Difference = 100

    mask_a = np.full((100, 100), 255, dtype=np.uint8)
    mask_a[50:, :] = 0 # Lower half invalid

    mask_b = np.full((100, 100), 255, dtype=np.uint8)
    mask_b[:, 50:] = 0 # Right half invalid

    # Mutually valid = upper-left quadrant (50x50 = 2500 pixels)
    H_identity = np.eye(3)
    b7_res = {"status": "SUCCESS", "homography": H_identity}

    res = reg.register(img_a, img_b, b7_res, mask_a=mask_a, mask_b=mask_b)
    metrics = res["metrics"]

    print(f"Valid count: {metrics['valid_pixel_count']}, MAE: {metrics['mae']}")
    assert metrics["valid_pixel_count"] == 2500
    assert np.isclose(metrics["mae"], 100.0)
    print("Valid region metrics test passed.")

def test_8_empty_valid_region():
    print("\n=== TEST 8: EMPTY VALID REGION ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img = np.ones((100, 100), dtype=np.uint8)
    mask_a = np.zeros((100, 100), dtype=np.uint8) # Completely invalid
    mask_b = np.full((100, 100), 255, dtype=np.uint8)

    H_identity = np.eye(3)
    b7_res = {"status": "SUCCESS", "homography": H_identity}

    res = reg.register(img, img, b7_res, mask_a=mask_a, mask_b=mask_b)
    assert res["status"] == "EMPTY_VALID_REGION"
    assert res["metrics"]["mae"] is None
    print("Empty valid region test passed.")

def test_9_input_validation():
    print("\n=== TEST 9: INPUT VALIDATION ===")
    from backend.pipeline.registration import ImageRegistration
    reg = ImageRegistration()

    img = np.ones((100, 100), dtype=np.uint8)
    b7_res = {"status": "SUCCESS", "homography": np.eye(3)}

    # None image
    res_none = reg.register(None, img, b7_res)
    assert res_none["status"] == "INVALID_INPUT"

    # Mismatched shapes (100x100 vs 50x50)
    img_small = np.ones((50, 50), dtype=np.uint8)
    res_shape = reg.register(img, img_small, b7_res)
    assert res_shape["status"] == "INVALID_INPUT"

    print("Input validation test passed.")

def test_10_b7_b8_integration():
    print("\n=== TEST 10: B7 -> B8 INTEGRATION ===")
    from backend.pipeline.ransac import RansacEstimator
    from backend.pipeline.registration import ImageRegistration

    estimator = RansacEstimator()
    reg = ImageRegistration()

    np.random.seed(42)
    src_pts = np.random.uniform(10, 200, (40, 2)).astype(np.float32)
    H_exact = np.array([[1.0, 0.0, 12.0], [0.0, 1.0, -8.0], [0.0, 0.0, 1.0]], dtype=np.float32)

    src_homo = np.hstack([src_pts, np.ones((40, 1), dtype=np.float32)])
    dst_homo = (H_exact @ src_homo.T).T
    dst_pts = (dst_homo[:, :2] / dst_homo[:, 2:3]).astype(np.float32)

    b7_res = estimator.estimate_from_points(src_pts, dst_pts)
    assert b7_res["status"] == "SUCCESS"

    img_a = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    img_b = img_a.copy()

    b8_res = reg.register(img_a, img_b, b7_res)
    print(f"B7->B8 Integration Status: {b8_res['status']}")
    assert b8_res["status"] == "SUCCESS"
    assert b8_res["registered_image"].shape == (256, 256)
    print("B7 -> B8 integration test passed.")

def test_11_end_to_end_sample_tile():
    print("\n=== TEST 11: END-TO-END B2 -> B5 -> B6 -> B7 -> B8 INTEGRATION ===")
    from backend.pipeline.loader import OHRCTileDataset
    from backend.pipeline.sift import SiftFeatureExtractor
    from backend.pipeline.matcher import FeatureMatcher
    from backend.pipeline.ransac import RansacEstimator
    from backend.pipeline.registration import ImageRegistration

    dataset = OHRCTileDataset(split="train")
    sample_a = dataset[0]
    sample_b = dataset[1]

    extractor = SiftFeatureExtractor()
    matcher = FeatureMatcher(method="bf", ratio_threshold=0.85)
    ransac = RansacEstimator(reprojection_threshold=5.0)
    registrator = ImageRegistration()

    feat_a = extractor.extract_from_sample(sample_a)
    feat_b = extractor.extract_from_sample(sample_b)

    match_res = matcher.match_features(feat_a, feat_b, split_a=sample_a.get("dataset_split"), split_b=sample_b.get("dataset_split"))
    ransac_res = ransac.estimate(match_res)
    b8_res = registrator.register(
        image_a=sample_a["preprocessed"],
        image_b=sample_b["preprocessed"],
        ransac_result=ransac_res,
        mask_a=sample_a.get("mask"),
        mask_b=sample_b.get("mask"),
        tile_a_id=sample_a.get("tile_id"),
        tile_b_id=sample_b.get("tile_id"),
    )

    print(f"Full Pipeline Integration Result on Tiles '{sample_a['tile_id']}' and '{sample_b['tile_id']}':")
    print(f"  B5 Features: {feat_a['count']} vs {feat_b['count']}")
    print(f"  B6 Match Status: {match_res['status']}, Filtered: {match_res['filtered_matches_count']}")
    print(f"  B7 RANSAC Status: {ransac_res['status']}, Inliers: {ransac_res['inlier_count']}")
    print(f"  B8 Registration Status: {b8_res['status']}")

    assert b8_res["status"] in ("SUCCESS", "INVALID_HOMOGRAPHY", "EMPTY_VALID_REGION")
    print("End-to-end sample tile test passed safely.")

def run_all():
    test_1_import()
    test_2_identity_homography()
    test_3_known_translation()
    test_4_invalid_homography()
    test_5_b7_failure_safety()
    test_6_mask_warping()
    test_7_valid_region_metrics()
    test_8_empty_valid_region()
    test_9_input_validation()
    test_10_b7_b8_integration()
    test_11_end_to_end_sample_tile()
    print("\nALL STEP 54 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
