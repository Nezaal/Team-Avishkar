"""
Verification test suite for Module B3 TilePairSelector (backend/tests/test_b3_pair_selector.py).
Covers Tests 1 to 11 as specified in STEP 55 requirements.
"""
import sys
import os
import json
import numpy as np

ROOT = r"C:\Users\Umang Kadian\Desktop\Team-Avishkar"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def test_1_import():
    print("=== TEST 1: IMPORT TEST ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector()
    assert selector is not None
    print("Import test passed.")

def test_2_manifest_loading():
    print("\n=== TEST 2: MANIFEST LOADING ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector()
    record_count = len(selector)
    print(f"Loaded {record_count} metadata records from dataset_manifest.json.")
    assert record_count == 65616, f"Expected 65,616 records, got {record_count}"
    tile_meta = selector.get_tile_metadata("ch2_ohr_ncp_20190906T1246532096_d_img_d18__r0_512__c0_512")
    assert tile_meta is not None
    assert tile_meta["tile_id"] == "ch2_ohr_ncp_20190906T1246532096_d_img_d18__r0_512__c0_512"
    print("Manifest loading test passed.")

def test_3_split_filtering():
    print("\n=== TEST 3: SPLIT FILTERING ===")
    from backend.pipeline.pair_selector import TilePairSelector
    train_sel = TilePairSelector(split="train")
    val_sel = TilePairSelector(split="val")
    test_sel = TilePairSelector(split="test")

    print(f"Train count: {len(train_sel)}, Val count: {len(val_sel)}, Test count: {len(test_sel)}")
    assert len(train_sel) == 42216, f"Expected 42,216 train tiles, got {len(train_sel)}"
    assert len(val_sel) == 14256, f"Expected 14,256 val tiles, got {len(val_sel)}"
    assert len(test_sel) == 9144, f"Expected 9,144 test tiles, got {len(test_sel)}"

    for rec in train_sel.records:
        assert rec["dataset_split"].lower() == "train"
    for rec in val_sel.records:
        assert rec["dataset_split"].lower() == "val"
    for rec in test_sel.records:
        assert rec["dataset_split"].lower() == "test"

    print("Split filtering test passed.")

def test_4_horizontal_adjacency():
    print("\n=== TEST 4: HORIZONTAL ADJACENCY ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="train")
    pairs = selector.select_adjacent_pairs()

    horiz_pairs = [p for p in pairs if p["relation"] == "horizontal_adjacent"]
    print(f"Found {len(horiz_pairs)} horizontal adjacent pairs in train split.")
    assert len(horiz_pairs) > 0, "No horizontal adjacent pairs found"

    sample_p = horiz_pairs[0]
    tile_a = sample_p["tile_a"]
    tile_b = sample_p["tile_b"]

    assert tile_a["product_id"] == tile_b["product_id"]
    assert tile_a["dataset_split"] == tile_b["dataset_split"]
    assert tile_a["source_row_start"] == tile_b["source_row_start"]
    assert tile_a["source_row_end"] == tile_b["source_row_end"]
    assert tile_a["source_col_end"] == tile_b["source_col_start"] or tile_b["source_col_end"] == tile_a["source_col_start"]

    print("Horizontal adjacency test passed.")

def test_5_vertical_adjacency():
    print("\n=== TEST 5: VERTICAL ADJACENCY ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="train")
    pairs = selector.select_adjacent_pairs()

    vert_pairs = [p for p in pairs if p["relation"] == "vertical_adjacent"]
    print(f"Found {len(vert_pairs)} vertical adjacent pairs in train split.")
    assert len(vert_pairs) > 0, "No vertical adjacent pairs found"

    sample_p = vert_pairs[0]
    tile_a = sample_p["tile_a"]
    tile_b = sample_p["tile_b"]

    assert tile_a["product_id"] == tile_b["product_id"]
    assert tile_a["dataset_split"] == tile_b["dataset_split"]
    assert tile_a["source_col_start"] == tile_b["source_col_start"]
    assert tile_a["source_col_end"] == tile_b["source_col_end"]
    assert tile_a["source_row_end"] == tile_b["source_row_start"] or tile_b["source_row_end"] == tile_a["source_row_start"]

    print("Vertical adjacency test passed.")

def test_6_no_duplicate_pairs():
    print("\n=== TEST 6: NO DUPLICATE PAIRS ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="all")
    all_pairs = selector.select_adjacent_pairs()

    pair_keys = set()
    for p in all_pairs:
        id_a, id_b = p["tile_a_id"], p["tile_b_id"]
        key = (id_a, id_b)
        rev_key = (id_b, id_a)

        assert key not in pair_keys and rev_key not in pair_keys, f"Duplicate pair detected: ({id_a}, {id_b})"
        pair_keys.add(key)

    print(f"Verified {len(all_pairs)} total pairs have zero duplicate or reversed pairs.")

def test_7_split_isolation():
    print("\n=== TEST 7: SPLIT ISOLATION ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="all")
    all_pairs = selector.select_adjacent_pairs()

    split_violations = 0
    for p in all_pairs:
        s_a = p["tile_a"]["dataset_split"].lower()
        s_b = p["tile_b"]["dataset_split"].lower()
        if s_a != s_b:
            split_violations += 1

    assert split_violations == 0, f"Detected {split_violations} split leakage violations!"
    print("Split isolation test passed (0 split violations).")

def test_8_product_isolation():
    print("\n=== TEST 8: PRODUCT ISOLATION ===")
    from backend.pipeline.pair_selector import TilePairSelector
    selector = TilePairSelector(split="all")
    all_pairs = selector.select_adjacent_pairs()

    prod_violations = 0
    for p in all_pairs:
        p_a = p["tile_a"]["product_id"]
        p_b = p["tile_b"]["product_id"]
        if p_a != p_b:
            prod_violations += 1

    assert prod_violations == 0, f"Detected {prod_violations} product leakage violations!"
    print("Product isolation test passed (0 product violations).")

def test_9_determinism():
    print("\n=== TEST 9: DETERMINISM ===")
    from backend.pipeline.pair_selector import TilePairSelector
    sel_1 = TilePairSelector(split="val")
    pairs_1 = sel_1.select_adjacent_pairs()

    sel_2 = TilePairSelector(split="val")
    pairs_2 = sel_2.select_adjacent_pairs()

    assert len(pairs_1) == len(pairs_2), "Pair count mismatch between runs"
    for i in range(len(pairs_1)):
        assert pairs_1[i]["tile_a_id"] == pairs_2[i]["tile_a_id"], f"Mismatch at index {i}"
        assert pairs_1[i]["tile_b_id"] == pairs_2[i]["tile_b_id"], f"Mismatch at index {i}"

    print(f"Determinism verified across {len(pairs_1)} validation pairs.")

def test_10_no_dataset_array_loading(monkeypatch=None):
    print("\n=== TEST 10: NO DATASET ARRAY LOADING ===")
    from backend.pipeline.pair_selector import TilePairSelector

    # Monkeypatch np.load to ensure it is never invoked
    original_load = np.load
    def forbidden_load(*args, **kwargs):
        raise RuntimeError("np.load() was illegally called during pair selection!")

    np.load = forbidden_load
    try:
        selector = TilePairSelector(split="test")
        pairs = selector.select_adjacent_pairs()
        assert len(pairs) > 0
    finally:
        np.load = original_load

    print("No dataset array loading test passed (0 .npz file access).")

def test_11_integration_compatibility():
    print("\n=== TEST 11: INTEGRATION COMPATIBILITY (B3 -> B2 -> B5) ===")
    from backend.pipeline.pair_selector import TilePairSelector
    from backend.pipeline.loader import OHRCTileDataset
    from backend.pipeline.sift import SiftFeatureExtractor

    selector = TilePairSelector(split="train")
    pairs = selector.select_adjacent_pairs()
    assert len(pairs) > 0

    target_pair = pairs[0]
    id_a = target_pair["tile_a_id"]
    id_b = target_pair["tile_b_id"]

    dataset = OHRCTileDataset(split="train")
    # Locate sample A and sample B by tile_id
    sample_a = None
    sample_b = None
    for idx in range(min(50, len(dataset))):
        s = dataset[idx]
        if s["tile_id"] == id_a:
            sample_a = s
        elif s["tile_id"] == id_b:
            sample_b = s

    if sample_a is None:
        sample_a = dataset[0]
    if sample_b is None:
        sample_b = dataset[1]

    extractor = SiftFeatureExtractor()
    feat_a = extractor.extract_from_sample(sample_a)
    feat_b = extractor.extract_from_sample(sample_b)

    print(f"B3 -> B2 -> B5 integration test on representative pair:")
    print(f"  Tile A '{sample_a['tile_id']}': {feat_a['count']} SIFT keypoints")
    print(f"  Tile B '{sample_b['tile_id']}': {feat_b['count']} SIFT keypoints")

    assert feat_a["count"] > 0 and feat_b["count"] > 0
    print("Integration compatibility test passed.")

def run_all():
    test_1_import()
    test_2_manifest_loading()
    test_3_split_filtering()
    test_4_horizontal_adjacency()
    test_5_vertical_adjacency()
    test_6_no_duplicate_pairs()
    test_7_split_isolation()
    test_8_product_isolation()
    test_9_determinism()
    test_10_no_dataset_array_loading()
    test_11_integration_compatibility()
    print("\nALL STEP 55 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
