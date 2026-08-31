# SIH26166 Ground Truth — Task List

> **Folder:** `ground_truth/`
> **Purpose:** Everything that needs to be done to complete the ground-truth dataset
> **Status as of:** 2026-08-31

---

## Current State Summary

| What | Status |
|------|--------|
| Pair metadata (20 pairs) | ✅ Done |
| Corner coordinates (OHRC, 25 scenes) | ✅ Done |
| 612 derived control points | ✅ Done (geographic interpolation only) |
| Pair directory structure (pair_001–020) | ✅ Done |
| Build script (`sources/build_dataset.py`) | ✅ Done |
| Synthetic GT CSV (5 transforms) | ✅ Done |
| OHRC image files | ❌ NOT downloaded (PRADAN login required) |
| TMC-2 image files | ❌ NOT downloaded (PRADAN login required) |
| TMC-2 image dimensions | ❌ UNKNOWN for all 20 pairs |
| TMC-2 pixel coords in control_points/ | ❌ All UNKNOWN |
| Exact TMC-2 product IDs (19 pairs) | ❌ Provisional names only |
| Manually annotated pixel correspondences | ❌ ZERO — none exist |
| LOLA DEM download (pair_012 region) | ❌ Not downloaded |

---

## 🔑 PRADAN Access — Prerequisite for Everything

**All image downloads require an ISRO PRADAN account.**

```
Portal: https://pradan.issdc.gov.in/ch2/
Login:  ISRO registered email required
```

> ⚠️ Without PRADAN access, Tasks GT-01 through GT-06 are blocked.
> Tasks GT-07 and GT-08 (IIT script + LOLA) can proceed without PRADAN.

**Action:** One team member must obtain PRADAN credentials before download begins.

---

## Task List

---

### GT-00 — PRADAN Account Setup

**Priority:** 🔴 MUST — blocks all image downloads
**Who:** Any team member with ISRO-eligible email
**Effort:** ~1 day (registration + approval)

**Steps:**
1. Register at https://pradan.issdc.gov.in/ch2/
2. Verify email and wait for approval
3. Log in and confirm access to OHRC + TMC-2 products
4. Share credentials securely with the download team member

**Done when:** Can successfully browse and download `.img` files from PRADAN.

---

### GT-01 — Download MVP OHRC Images (Priority 3 pairs)

**Priority:** 🔴 MUST — needed for CV pipeline testing
**Depends on:** GT-00 (PRADAN access)
**Who:** Data team
**Effort:** ~2 hours per image (large files)

Download the 3 MVP pairs first (Pair A, B, C):

| Pair | OHRC Product ID | File | Region | Purpose |
|------|----------------|------|--------|---------|
| pair_001 | `ch2_ohr_ncp_20200825T1127278043_d_img_d18` | `.img` | South Polar 41°E | Demo pair (Pair A) |
| pair_012 | `ch2_ohr_ncp_20200827T0226453039_d_img_d18` | `.img` | South Polar 20°E | LOLA-referenced (Pair B) |
| pair_003 | `ch2_ohr_ncp_20200229T0739312111_d_img_d18` | `.img` | South Polar 43°E | Difficult pair (Pair C) |

**Where to place:**
```
ground_truth/pairs/pair_001/raw/ch2_ohr_ncp_20200825T1127278043_d_img_d18.img
ground_truth/pairs/pair_012/raw/ch2_ohr_ncp_20200827T0226453039_d_img_d18.img
ground_truth/pairs/pair_003/raw/ch2_ohr_ncp_20200229T0739312111_d_img_d18.img
```

**Done when:** 3 `.img` files present in correct `raw/` directories.

---

### GT-02 — Download MVP TMC-2 Images (Priority 3 pairs)

**Priority:** 🔴 MUST — needed for CV pipeline testing
**Depends on:** GT-00 (PRADAN access), GT-07 (exact TMC-2 product IDs)
**Who:** Data team
**Effort:** ~2 hours per image

For pair_012, the exact TMC-2 product ID is known:

| Pair | TMC-2 Product ID | File | Source |
|------|-----------------|------|--------|
| pair_012 | `ch2_tmc_ndn_20231101T0125121377_d_oth_d18` | `.img` | USGS/ASP documented |
| pair_001 | `ch2_tmc_ncn_SouthPolar_41E_grd` (PROVISIONAL) | `.img` | Run GT-07 first to confirm |
| pair_003 | `ch2_tmc_ncn_SouthPolar_43E_grd` (PROVISIONAL) | `.img` | Run GT-07 first to confirm |

**Where to place:**
```
ground_truth/pairs/pair_012/raw/ch2_tmc_ndn_20231101T0125121377_d_oth_d18.img
ground_truth/pairs/pair_001/raw/<confirmed_tmc2_product>.img
ground_truth/pairs/pair_003/raw/<confirmed_tmc2_product>.img
```

**Done when:** 3 TMC-2 `.img` files present in correct `raw/` directories.

---

### GT-03 — Extract TMC-2 Image Dimensions

**Priority:** 🔴 MUST — needed to compute TMC-2 pixel coordinates
**Depends on:** GT-02 (at least 1 TMC-2 image downloaded)
**Who:** Data team / CV team
**Effort:** ~30 minutes

**Steps:**
1. For each downloaded TMC-2 `.img` file, read the PDS header to extract `LINES` and `LINE_SAMPLES` (= height and width)
2. Update `pairs.csv` column `reference_width` and `reference_height`
3. Update relevant `metadata.json` files

```python
# Quick PDS header reader
with open("ch2_tmc_ndn_20231101T0125121377_d_oth_d18.img", "rb") as f:
    header = f.read(4096).decode("ascii", errors="ignore")
    # Look for: LINES = NNNN and LINE_SAMPLES = NNNN
    print(header[:2000])
```

**Done when:** `reference_width` and `reference_height` are populated in pairs.csv for the 3 MVP pairs.

---

### GT-04 — Recompute TMC-2 Pixel Coordinates in Control Points

**Priority:** 🔴 MUST — needed for ground-truth validation
**Depends on:** GT-03 (TMC-2 dimensions known)
**Who:** Data team
**Effort:** ~1 hour (run script)

**Steps:**
1. Once TMC-2 `width` and `height` are known, re-run `sources/build_dataset.py`
2. The script will populate `reference_x` and `reference_y` in control point CSVs
3. Verify output: `control_points/pair_001.csv` should have non-UNKNOWN reference coords

```bash
cd ground_truth/sources
python build_dataset.py
```

**Done when:** `reference_x` and `reference_y` are non-null in at least 3 pair CP CSVs.

---

### GT-05 — Manual Pixel Annotation (Pairs A, B, C)

**Priority:** 🟡 SHOULD — needed for any sub-pixel accuracy claim
**Depends on:** GT-01 + GT-02 (images downloaded)
**Who:** CV team (manual annotation using image viewer)
**Effort:** ~2–3 hours per pair

Manually annotate **30+ pixel-exact correspondences** for each MVP pair.

**Tool options:**
- QGIS (load .img as raster, manually pick points)
- NASA JMARS
- Python + matplotlib (click-to-annotate script)
- Any image viewer that shows pixel coordinates

**Format for each annotation:**
```csv
point_id,source_x,source_y,reference_x,reference_y,annotation_method,annotator
manual_001_1,1024.5,2048.3,512.1,1024.8,visual_landmark,TeamMember1
```

**Save to:**
```
ground_truth/control_points/manual/pair_001_manual.csv
ground_truth/control_points/manual/pair_012_manual.csv
ground_truth/control_points/manual/pair_003_manual.csv
```

**Done when:** 30+ manual annotations exist for pair_001 and pair_012.

---

### GT-06 — Download All 20 OHRC + TMC-2 Images (Full Dataset)

**Priority:** 🟢 NICE — for comprehensive validation beyond MVP
**Depends on:** GT-00 (PRADAN access), GT-07 (exact product IDs)
**Who:** Data team
**Effort:** ~1–2 days (large files, ~1–10 GB per image)

Download remaining 17 pairs after MVP pairs are confirmed working.

**Pairs to download (after MVP pairs done):**
pair_002, pair_004–011, pair_013–020

> ⚠️ Check available disk space before bulk download. OHRC images can be 1–5 GB each.

**Done when:** All 20 pairs have both OHRC and TMC-2 `.img` files in their `raw/` directories.

---

### GT-07 — Run IIT Overlap Script to Get Exact TMC-2 Product IDs

**Priority:** 🔴 MUST — needed before GT-02 for 19 pairs
**Depends on:** Nothing (no images required — uses CSVs already downloaded)
**Who:** Data team
**Effort:** ~1 hour

**Steps:**
1. Clone the IIT repository:
   ```bash
   git clone https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0
   ```
2. Run their overlap detection script against our CSVs:
   ```bash
   cd ISRO-InterIIT-Techmeet-11.0
   python ohrc_tmc_overlap.py \
     --ohrc ../ground_truth/sources/coordinates_ohrc_iit.csv \
     --tmc2 ../ground_truth/sources/coordinates_tmc2_iit.csv
   ```
3. Record the 6 exact TMC-2 product IDs that match our 25 OHRC scenes
4. Update `manifests/pairs.csv` column `reference_image_id` (currently PROVISIONAL for 19 pairs)
5. Update all 19 `metadata.json` files with exact TMC-2 filenames

**Exact ID already known (no script needed):**
- pair_012: `ch2_tmc_ndn_20231101T0125121377_d_oth_d18` (from USGS/ASP)

**Done when:** All 20 rows in `pairs.csv` have exact (non-provisional) `reference_image_id`.

---

### GT-08 — Download LOLA DEM for pair_012 Independent Validation

**Priority:** 🟡 SHOULD — strengthens the scientific case for pair_012
**Depends on:** Nothing (LOLA is publicly available without login)
**Who:** Data team
**Effort:** ~1 hour

**Steps:**
1. Go to: https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
2. Download `LDEM_60S_120M` (120m/px south polar DEM) — covers pair_012 region
3. Clip to pair_012 bounding box: **67–71°S, 19–22°E**
4. Save to:
   ```
   ground_truth/pairs/pair_012/raw/LDEM_60S_120M_clip.img
   ```
5. Optionally download `LDEM_75S` (higher resolution, same region)

**Purpose:** Provides an independent (non-Chandrayaan-2) elevation reference for pair_012 validation.

**Done when:** LOLA DEM file clipped to pair_012 region is present in `pairs/pair_012/raw/`.

---

### GT-09 — Update build_dataset.py After TMC-2 Dims Known

**Priority:** 🔴 MUST (after GT-03)
**Depends on:** GT-03 (TMC-2 dims), GT-07 (exact product IDs)
**Who:** Data team
**Effort:** ~30 minutes

Once TMC-2 dimensions are known:
1. Edit `sources/build_dataset.py` to hardcode the confirmed dims
2. Re-run script to regenerate all control point CSVs with real `reference_x`/`reference_y`
3. Run validation check: confirm no UNKNOWN values remain for downloaded pairs

**Done when:** `build_dataset.py` re-run successfully, `reference_x`/`reference_y` populated.

---

### GT-10 — Verify Synthetic Validation Dataset

**Priority:** 🔴 MUST — needed by backend before real images arrive
**Depends on:** Nothing (no PRADAN needed)
**Who:** CV/Backend team
**Effort:** ~30 minutes

The file `ground_truth/validation/synthetic/synthetic_gt.csv` contains 5 known transforms.

**Verify:**
1. Open `synthetic_gt.csv` and confirm all 5 transform types are present
2. Confirm the backend can read the transform parameters
3. Apply each transform to a test grayscale image
4. Run full pipeline on (original, transformed) pair
5. Check that recovered homography ≈ known transform

**Done when:** Backend's synthetic validation module passes all 5 transform types.

---

## Summary by Assignee Type

### 🔑 Data Team Tasks (no CV coding)

| Task | Depends on | Effort |
|------|-----------|--------|
| GT-00 — PRADAN account | — | ~1 day |
| GT-07 — Run IIT overlap script | Nothing | ~1 hour |
| GT-08 — Download LOLA DEM | Nothing | ~1 hour |
| GT-01 — Download 3 OHRC images | GT-00 | ~6 hours |
| GT-02 — Download 3 TMC-2 images | GT-00, GT-07 | ~6 hours |
| GT-03 — Extract TMC-2 dims | GT-02 | ~30 min |
| GT-04 — Recompute control points | GT-03 | ~1 hour |
| GT-06 — Download all 20 images | GT-00, GT-07 | ~1–2 days |

### 🔬 CV / Annotation Team Tasks

| Task | Depends on | Effort |
|------|-----------|--------|
| GT-05 — Manual annotation pairs A/B/C | GT-01, GT-02 | ~6–9 hours |
| GT-10 — Verify synthetic validation | Nothing | ~30 min |

### 💻 Script / Dev Team Tasks

| Task | Depends on | Effort |
|------|-----------|--------|
| GT-07 — Run IIT overlap script | Nothing | ~1 hour |
| GT-09 — Update build_dataset.py | GT-03, GT-07 | ~30 min |

---

## Minimum to Unblock the CV Pipeline

The CV pipeline (backend) can start with **synthetic images only** right now.
To test on real lunar images, the minimum required is:

```
GT-07  → exact TMC-2 IDs (run IIT script — no PRADAN needed)  ← DO THIS NOW
GT-00  → PRADAN access
GT-01  → download pair_001 OHRC image
GT-02  → download pair_001 TMC-2 image
GT-03  → read image dimensions
GT-04  → recompute control point pixel coords
```

**GT-07 can be done immediately without any PRADAN account.**

---

## File Placement Reference

```
ground_truth/
├── pairs/
│   ├── pair_001/raw/     ← ch2_ohr_ncp_20200825T1127278043_d_img_d18.img  (GT-01)
│   │                     ← <confirmed_tmc2_product>.img                    (GT-02)
│   ├── pair_003/raw/     ← ch2_ohr_ncp_20200229T0739312111_d_img_d18.img  (GT-01)
│   │                     ← <confirmed_tmc2_product>.img                    (GT-02)
│   └── pair_012/raw/     ← ch2_ohr_ncp_20200827T0226453039_d_img_d18.img  (GT-01)
│                         ← ch2_tmc_ndn_20231101T0125121377_d_oth_d18.img  (GT-02)
│                         ← LDEM_60S_120M_clip.img                         (GT-08)
├── control_points/
│   └── manual/           ← pair_001_manual.csv, pair_012_manual.csv        (GT-05)
└── sources/
    └── build_dataset.py  ← re-run after GT-03                              (GT-09)
```

---

*Last updated: 2026-08-31 | Team Avishkar — SIH26166*
