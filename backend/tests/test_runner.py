"""
Verification test suite for PipelineRunner & FastAPI integration (backend/tests/test_runner.py).
Covers Tests 1 to 11 as specified in STEP 56 requirements.
"""
import sys
import os
import json

ROOT = r"C:\Users\Umang Kadian\Desktop\Team-Avishkar"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_1_import():
    print("=== TEST 1: IMPORT TEST ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()
    assert runner is not None
    print("Import test passed.")

def test_2_runner_initialization():
    print("\n=== TEST 2: RUNNER INITIALIZATION ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()
    assert hasattr(runner, "run_pair")
    assert hasattr(runner, "run_selected_pair")
    assert hasattr(runner, "get_dataset_info")
    print("Runner initialization test passed.")

def test_3_dataset_metadata():
    print("\n=== TEST 3: DATASET METADATA ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()
    info = runner.get_dataset_info()

    print(f"Dataset info: {info}")
    assert info["dataset"] == "OHRC"
    assert info["total_tiles"] == 65616
    assert info["splits"]["train"] == 42216
    assert info["splits"]["val"] == 14256
    assert info["splits"]["test"] == 9144
    assert info["tile_size"] == [512, 512]
    print("Dataset metadata test passed.")

def test_4_b3_pair_selection():
    print("\n=== TEST 4: B3 PAIR SELECTION ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="train")
    pairs = selector.select_adjacent_pairs()

    assert len(pairs) > 0, "No adjacent pairs returned"
    sample_pair = pairs[0]
    print(f"Selected sample pair: {sample_pair['tile_a_id']} & {sample_pair['tile_b_id']}")

    assert sample_pair["product_id"] is not None
    assert sample_pair["dataset_split"] == "train"
    assert sample_pair["tile_a_id"] != sample_pair["tile_b_id"]
    print("B3 pair selection test passed.")

def test_5_full_pipeline_integration():
    print("\n=== TEST 5: FULL PIPELINE INTEGRATION (ONE PAIR) ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()

    res = runner.run_selected_pair(split="train", mode="adjacent")
    print(f"Pipeline Execution Status: {res['status']}, Stage: {res['pipeline_stage']}")
    print(f"  Tile A: {res['tile_a_id']}, Tile B: {res['tile_b_id']}")
    print(f"  Feature Metrics: {res['feature_metrics']}")
    print(f"  Matching Metrics: {res['matching_metrics']}")
    print(f"  RANSAC Metrics: {res['ransac_metrics']}")
    print(f"  Registration Metrics: {res['registration_metrics']}")

    assert "status" in res
    assert "feature_metrics" in res
    assert "matching_metrics" in res
    assert "ransac_metrics" in res
    assert "registration_metrics" in res
    print("Full pipeline integration test passed.")

def test_6_cross_split_protection():
    print("\n=== TEST 6: CROSS SPLIT PROTECTION ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()

    meta_train = runner.selector.records[0] # Train tile
    # Find a validation tile
    meta_val = next(r for r in runner.selector.records if (r.get("dataset_split") or r.get("split", "")).lower() == "val")

    res = runner.run_pair(meta_train["tile_id"], meta_val["tile_id"])
    print(f"Cross-split response status: {res['status']}")
    assert res["status"] in ("CROSS_SPLIT_PROHIBITED", "CROSS_PRODUCT_PROHIBITED")
    print("Cross split protection test passed.")

def test_7_invalid_tile_id():
    print("\n=== TEST 7: INVALID TILE ID ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()

    res = runner.run_pair("fake_tile_id_999", "ch2_ohr_ncp_20190906T1246532096_d_img_d18__r0_512__c0_512")
    assert res["status"] == "TILE_NOT_FOUND"
    print("Invalid tile ID test passed.")

def test_8_json_serialization():
    print("\n=== TEST 8: JSON SERIALIZATION ===")
    from backend.pipeline.runner import PipelineRunner
    runner = PipelineRunner()

    res = runner.run_selected_pair(split="train", mode="adjacent")
    json_str = json.dumps(res)
    assert len(json_str) > 0
    parsed = json.loads(json_str)
    assert parsed["status"] == res["status"]
    print("JSON serialization test passed.")

def test_9_dataset_info_api():
    print("\n=== TEST 9: DATASET INFO API ===")
    from backend.api.server import get_dataset_info
    info = get_dataset_info()
    assert info["total_tiles"] == 65616
    print("Dataset info API test passed.")

def test_10_fastapi_health():
    print("\n=== TEST 10: FASTAPI HEALTH ===")
    from fastapi.testclient import TestClient
    from backend.api.server import app

    client = TestClient(app)
    response = client.get("/health")
    print(f"Health Response: {response.status_code} - {response.json()}")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("FastAPI health test passed.")

def test_11_fastapi_sample_pipeline():
    print("\n=== TEST 11: FASTAPI SAMPLE PIPELINE ===")
    from fastapi.testclient import TestClient
    from backend.api.server import app

    client = TestClient(app)
    response = client.get("/pipeline/sample?split=train&mode=adjacent")
    print(f"Sample Pipeline Response Status: {response.status_code}")
    assert response.status_code == 200
    res_json = response.json()
    assert "status" in res_json
    assert "feature_metrics" in res_json
    assert "matching_metrics" in res_json
    print("FastAPI sample pipeline test passed.")

def run_all():
    test_1_import()
    test_2_runner_initialization()
    test_3_dataset_metadata()
    test_4_b3_pair_selection()
    test_5_full_pipeline_integration()
    test_6_cross_split_protection()
    test_7_invalid_tile_id()
    test_8_json_serialization()
    test_9_dataset_info_api()
    test_10_fastapi_health()
    test_11_fastapi_sample_pipeline()
    print("\nALL STEP 56 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
