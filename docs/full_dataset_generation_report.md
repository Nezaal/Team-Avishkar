# STEP 46 — Full Dataset Generation & Recovery Report

## Executive Summary

- **Pipeline Step**: STEP 46 — Full 36-Product Dataset Generation & Crash Recovery
- **Dataset Name**: `Chandrayaan2_Full_36_Product_Dataset`
- **Total Products**: 36 Remote PDS4 Datasets (15 OHRC, 21 TMC-2)
- **Total Expected Tiles**: 152,520 NPZ tiles (512x512 native resolution)
- **Recovery Event**: Laptop / Antivirus crash during initial STEP 46 execution.
- **Recovery Mode**: Checkpoint-based resumption without zero-start or duplicate tile generation.

---

## STEP 46 — CRASH/POWER-LOSS RECOVERY AUDIT

### 1. Interruption Context & Discovery
- **Time of Interruption**: Prior to system reboot.
- **Root Directory**: `dataset/streaming_dataset`
- **Manifest Location**: `dataset/streaming_dataset/dataset_manifest.json`
- **Tiles Location**: `dataset/streaming_dataset/tiles/<product_id>/`

### 2. Orphan File & Temporary Artifact Clearance
- **Orphan Temporary Files Found**: 0 (`*.tmp`, `*.npz.tmp`, `dataset_manifest.json.tmp`)
- **Loose Tile Migration**: 0 (all tiles properly housed in product directories)
- **Corrupted / Truncated NPZ Files Removed**: 0

### 3. Verification & Reconciled Checkpoint State
Every existing tile was subjected to strict multi-threaded integrity validation:
- NPZ archive openability and key existence (`raw`, `preprocessed`, `mask`)
- Dimensions exact match with expected bounds (`tile_height` x `tile_width`)
- Preprocessed image dtype == `uint8`
- Mask image dtype in (`uint8`, `bool`) with valid values `{0, 255}`
- Source raw dtype verification: `uint8` for OHRC, `uint16` (`>u2`) for TMC-2
- Range & sanity checks: No `NaN` or `Inf` in raw or preprocessed layers
- Manifest record alignment: `product_id`, spatial bounds (`r_start`, `r_end`, `c_start`, `c_end`) match tile ID

#### Recovery Table Summary

| Idx | Product ID | Sensor | Expected Tiles | Valid Existing Tiles | Missing / Invalid | Status |
|---|---|---|---|---|---|---|
| 01 | `ch2_ohr_ncp_20190906T1246532096_d_img_d18` | OHRC | 2,976 | 2,976 | 0 | **COMPLETE** |
| 02 | `ch2_ohr_ncp_20200229T0739312111_d_img_d18` | OHRC | 4,392 | 4,392 | 0 | **COMPLETE** |
| 03 | `ch2_ohr_ncp_20200229T0938004033_d_img_d32` | OHRC | 4,392 | 4,392 | 0 | **COMPLETE** |
| 04 | `ch2_ohr_ncp_20200824T0806596861_d_img_d18` | OHRC | 4,248 | 4,248 | 0 | **COMPLETE** |
| 05 | `ch2_ohr_ncp_20200824T1003365280_d_img_d18` | OHRC | 4,392 | 576 | 3,816 | **INTERRUPTED (576/4392)** |
| 06–15 | OHRC Products 06–15 | OHRC | 44,976 | 0 | 44,976 | NOT STARTED |
| 16–36 | TMC-2 Products 16–36 | TMC-2 | 87,144 | 0 | 87,144 | NOT STARTED |
| **TOTAL** | **36 Products** | **Both** | **152,520** | **16,584** | **135,936** | **RESUMING AT PRODUCT 05 TILE 577** |

### 4. Recovery Audit Results
- **Detected Completed Products**: 4 Products (`01`, `02`, `03`, `04`)
- **Interrupted Product**: Product 05 (`ch2_ohr_ncp_20200824T1003365280_d_img_d18`)
- **Tiles Recovered & Preserved**: 16,584 tiles (100% verified)
- **Tiles Skipped (Already Valid)**: 16,584 tiles
- **Tiles Regenerated / Removed as Invalid**: 0 tiles
- **Manifest Reconciliation**: `dataset_manifest.json` updated atomically with 16,584 valid tile records.
- **Resume Starting Point**: Product 05, Row Strip 24 (Tile ID `ch2_ohr_ncp_20200824T1003365280_d_img_d18__r12288_12800__c0_512`).

---

## RESUME PIPELINE EXECUTION & DISK SAFETY

- **Free Disk Space at Resume**: 93.81 GB
- **Estimated Storage Required for Remaining Tiles**: ~36.04 GB
- **Hard Disk Reserve Enforced**: 10.00 GB
- **Disk Safety Status**: **PASSED** (93.81 GB > 46.04 GB required minimum)
- **Current Status**: Background streaming generation running product-by-product.

---

## DECISION

**READY WITH REQUIRED FIXES** (Crash state successfully audited and reconciled; full dataset streaming generation actively resuming from checkpoint tile 577 of Product 05 towards 100% completion across all 36 products).
