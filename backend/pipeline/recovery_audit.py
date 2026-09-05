"""
STEP 46 Recovery Audit Script
Validates dataset manifest against filesystem, checks existing NPZ tile integrity,
cleans orphan temp files, and prints the Recovery Table.
"""
import os
import sys
import json
import math
import glob
import builtins
import numpy as np
from concurrent.futures import ThreadPoolExecutor

os.environ["PYTHONUNBUFFERED"] = "1"

def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    builtins.print(*args, **kwargs)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

CATALOG_PATH = os.path.join(ROOT, "ground_truth", "product_catalog.json")
DATASET_DIR = os.path.join(ROOT, "dataset", "streaming_dataset")
TILES_DIR = os.path.join(DATASET_DIR, "tiles")
MANIFEST_PATH = os.path.join(DATASET_DIR, "dataset_manifest.json")
TILE_SIZE = 512

def calculate_product_grid(width: int, height: int):
    n_cols = math.ceil(width / TILE_SIZE)
    n_rows = math.ceil(height / TILE_SIZE)
    return n_rows, n_cols, n_rows * n_cols

def validate_tile(tile_args):
    tile_path, pid, sensor, expected_tile_w, expected_tile_h, r_start, r_end, c_start, c_end, tile_id, manifest_tiles = tile_args
    if not os.path.exists(tile_path):
        return False, tile_id, "missing file", None
    try:
        st = os.stat(tile_path)
        if st.st_size < 100:
            return False, tile_id, f"truncated file ({st.st_size} bytes)", tile_path
        with np.load(tile_path) as data:
            keys = set(data.files)
            if keys != {"raw", "preprocessed", "mask"}:
                return False, tile_id, f"invalid keys: {keys}", tile_path
            raw = data["raw"]
            prep = data["preprocessed"]
            mask = data["mask"]

            expected_shape = (expected_tile_h, expected_tile_w)
            if raw.shape != expected_shape or prep.shape != expected_shape or mask.shape != expected_shape:
                return False, tile_id, f"shape mismatch: raw={raw.shape}, prep={prep.shape}, mask={mask.shape}", tile_path
            if prep.dtype != np.uint8:
                return False, tile_id, f"prep dtype {prep.dtype} != uint8", tile_path
            if mask.dtype not in (np.uint8, np.bool_):
                return False, tile_id, f"mask dtype {mask.dtype} invalid", tile_path
            if sensor == "OHRC" and raw.dtype != np.uint8:
                return False, tile_id, f"raw dtype {raw.dtype} != uint8 for OHRC", tile_path
            if sensor == "TMC-2" and not (raw.dtype.kind == 'u' and raw.dtype.itemsize == 2):
                return False, tile_id, f"raw dtype {raw.dtype} != uint16 for TMC-2", tile_path
            if tile_id not in manifest_tiles:
                return False, tile_id, "missing manifest record", tile_path

            rec = manifest_tiles[tile_id]
            if rec.get("product_id") != pid:
                return False, tile_id, "manifest product_id mismatch", tile_path
            if rec.get("source_row_start") != r_start or rec.get("source_row_end") != r_end or rec.get("source_col_start") != c_start or rec.get("source_col_end") != c_end:
                return False, tile_id, "manifest row/col bounds mismatch", tile_path
            if np.isnan(raw).any() or np.isnan(prep).any() or np.isinf(raw).any() or np.isinf(prep).any():
                return False, tile_id, "contains NaN or Inf", tile_path
            if not np.isin(mask, [0, 255]).all() and mask.dtype != np.bool_:
                return False, tile_id, "mask values outside {0, 255}", tile_path

        return True, tile_id, "", None
    except Exception as e:
        return False, tile_id, f"failed to load: {e}", tile_path

def audit():
    print("=" * 105)
    print("STEP 46 — RECOVERY AUDIT & TILE INTEGRITY VERIFICATION")
    print("=" * 105)

    # 1. Load catalog
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)["products"]

    # 2. Check for temp files & loose tiles
    orphan_tmps = []
    for root_dir, _, files in os.walk(DATASET_DIR):
        for f in files:
            if f.endswith(".tmp") or f.endswith("_tmp.npz"):
                orphan_tmps.append(os.path.join(root_dir, f))

    print(f"[TMP SEARCH] Found {len(orphan_tmps)} orphan temporary files:")
    for tmp in orphan_tmps:
        print(f"  - {tmp}")
        try:
            os.remove(tmp)
            print(f"    -> Successfully removed orphan temp file: {tmp}")
        except Exception as e:
            print(f"    -> Failed to remove {tmp}: {e}")

    # Reorganize loose tiles if any exist directly in TILES_DIR
    moved_loose = 0
    if os.path.exists(TILES_DIR):
        for f in os.listdir(TILES_DIR):
            f_path = os.path.join(TILES_DIR, f)
            if f.endswith(".npz") and not os.path.isdir(f_path):
                pid = f.split("__r")[0]
                p_dir = os.path.join(TILES_DIR, pid)
                os.makedirs(p_dir, exist_ok=True)
                os.replace(f_path, os.path.join(p_dir, f))
                moved_loose += 1
    if moved_loose > 0:
        print(f"[RECOVERY] Reorganized {moved_loose} loose tile files into product directories.")

    # 3. Load manifest
    manifest = {}
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"[MANIFEST] Loaded existing dataset_manifest.json with {len(manifest.get('tiles', {}))} tile records.")
    else:
        print("[MANIFEST] dataset_manifest.json NOT FOUND!")
        return

    manifest_tiles = manifest.get("tiles", {})

    # 4. Audit products tile by tile
    table_rows = []
    reconciled_tiles = {}
    corrupted_count = 0
    total_valid_tiles = 0
    total_expected_tiles = 0

    executor = ThreadPoolExecutor(max_workers=16)

    for idx, prod in enumerate(catalog, 1):
        pid = prod["product_id"]
        sensor = prod["sensor"]
        w, h = prod["width"], prod["height"]
        n_rows, n_cols, expected_tiles = calculate_product_grid(w, h)
        total_expected_tiles += expected_tiles

        prod_dir = os.path.join(TILES_DIR, pid)
        valid_tiles_for_prod = 0
        invalid_tiles_for_prod = 0

        if not os.path.exists(prod_dir):
            status = "NOT STARTED"
            table_rows.append({
                "idx": idx,
                "pid": pid,
                "sensor": sensor,
                "expected": expected_tiles,
                "valid": 0,
                "invalid_missing": expected_tiles,
                "status": status
            })
            print(f"[{idx:02d}/36] Audited {pid[:35]}... -> {status} (0/{expected_tiles} valid)")
            continue

        # Prepare tile validation tasks
        tasks = []
        for r_idx in range(n_rows):
            r_start = r_idx * TILE_SIZE
            r_end = min(r_start + TILE_SIZE, h)
            expected_tile_h = r_end - r_start

            for c_idx in range(n_cols):
                c_start = c_idx * TILE_SIZE
                c_end = min(c_start + TILE_SIZE, w)
                expected_tile_w = c_end - c_start

                tile_id = f"{pid}__r{r_start}_{r_end}__c{c_start}_{c_end}"
                tile_path = os.path.join(prod_dir, f"{tile_id}.npz")
                tasks.append((tile_path, pid, sensor, expected_tile_w, expected_tile_h, r_start, r_end, c_start, c_end, tile_id, manifest_tiles))

        results = executor.map(validate_tile, tasks)
        for is_valid, tile_id, err_reason, bad_path in results:
            if is_valid:
                valid_tiles_for_prod += 1
                reconciled_tiles[tile_id] = manifest_tiles[tile_id]
            else:
                invalid_tiles_for_prod += 1
                if bad_path and os.path.exists(bad_path):
                    print(f"[INVALID TILE DETECTED] Removing {bad_path}: {err_reason}")
                    try:
                        os.remove(bad_path)
                    except Exception as e_rm:
                        print(f"  -> Error removing file: {e_rm}")
                    corrupted_count += 1

        total_valid_tiles += valid_tiles_for_prod

        if valid_tiles_for_prod == expected_tiles:
            status = "COMPLETE"
        elif valid_tiles_for_prod > 0:
            status = f"INTERRUPTED ({valid_tiles_for_prod}/{expected_tiles})"
        else:
            status = "NOT STARTED"

        table_rows.append({
            "idx": idx,
            "pid": pid,
            "sensor": sensor,
            "expected": expected_tiles,
            "valid": valid_tiles_for_prod,
            "invalid_missing": invalid_tiles_for_prod,
            "status": status
        })
        print(f"[{idx:02d}/36] Audited {pid[:35]}... -> {status} ({valid_tiles_for_prod}/{expected_tiles} valid)")

    executor.shutdown(wait=True)

    # Print Recovery Table
    print("\n" + "=" * 105)
    print("RECOVERY AUDIT COMPLETE")
    print("=" * 105)
    print(f"{'Idx':3s} | {'Product ID':42s} | {'Sensor':6s} | {'Expected':9s} | {'Valid Existing':14s} | {'Missing/Invalid':15s} | {'Resume Status':20s}")
    print("-" * 105)

    interrupted_product = None
    completed_products = []

    for r in table_rows:
        print(f"{r['idx']:02d}  | {r['pid']:42s} | {r['sensor']:6s} | {r['expected']:9d} | {r['valid']:14d} | {r['invalid_missing']:15d} | {r['status']:20s}")
        if r['status'] == "COMPLETE":
            completed_products.append(r['pid'])
        elif "INTERRUPTED" in r['status']:
            interrupted_product = r['pid']

    print("-" * 105)
    print(f"Total Expected Dataset Tiles: {total_expected_tiles:,}")
    print(f"Total Valid Existing Tiles:   {total_valid_tiles:,}")
    print(f"Total Missing / Invalid:      {total_expected_tiles - total_valid_tiles:,}")
    print(f"Completed Products Count:     {len(completed_products)} / {len(catalog)}")
    print(f"Interrupted Product ID:       {interrupted_product if interrupted_product else 'None'}")
    print("=" * 105 + "\n")

    # Update manifest cleanly without resetting or destroying progress
    manifest["tiles"] = reconciled_tiles
    manifest["total_tiles"] = len(reconciled_tiles)
    manifest["completed_products"] = completed_products

    tmp_manifest = MANIFEST_PATH + ".tmp"
    with open(tmp_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp_manifest, MANIFEST_PATH)
    print(f"[RECONCILED MANIFEST] Atomic update complete. Preserved {len(reconciled_tiles)} valid tiles across {len(completed_products)} completed products.")

if __name__ == "__main__":
    audit()
