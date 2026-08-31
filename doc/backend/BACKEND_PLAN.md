# SIH26166 Backend — Module Task Plan

> **Priority:** 🔴 MUST | 🟡 SHOULD | 🟢 NICE  
> **Stack:** Python 3.10+, OpenCV, NumPy, FastAPI

---

## Pre-Work: Contract First

Before any backend code, create:

```
contracts/result.schema.json
contracts/example_result.json
```

This is the interface the frontend will depend on. Do not change this schema
without coordinating with the frontend team.

---

## B1 — Skeleton 🔴 MUST

**Create directory structure:**

```
backend/
├── api/server.py
├── pipeline/
│   ├── loader.py
│   ├── pair_analyzer.py
│   ├── preprocessor.py
│   ├── sift.py
│   ├── matcher.py
│   ├── ransac.py
│   ├── registration.py
│   └── runner.py
├── validation/
│   ├── ground_truth.py
│   └── synthetic.py
├── models/result.py
├── tests/
└── README.md
```

**Acceptance:**
- [ ] `python -m backend.api.server` starts without error
- [ ] `GET /health` returns `{"status": "ok"}`

---

## B2 — Image Loader 🔴 MUST

**File:** `backend/pipeline/loader.py`

**Input:** file path (TIFF or PDS IMG)

**Output:**
```python
{
    "array": np.ndarray,     # image data
    "width": int,
    "height": int,
    "channels": int,
    "dtype": str,
    "metadata": dict         # band info, resolution if in header
}
```

**Acceptance:**
- [ ] Loads TIFF without error
- [ ] Returns correct dimensions
- [ ] Handles grayscale and multi-band

---

## B3 — Pair Analyzer 🔴 MUST

**File:** `backend/pipeline/pair_analyzer.py`

**Input:** two loaded image dicts (source + reference)

**Output:**
```python
{
    "resolution_ratio": float,    # reference_res / source_res
    "scale_factor": float,        # pixel scale difference
    "source_contrast": float,
    "reference_contrast": float,
    "texture_score": float,
    "blur_score": float,
    "working_scale": float        # recommended resize factor
}
```

**Acceptance:**
- [ ] Computes resolution ratio
- [ ] Returns recommended working scale
- [ ] No crash on 2048×2048 OHRC input

---

## B4 — Preprocessing 🔴 MUST

**File:** `backend/pipeline/preprocessor.py`

**Operations (in order):**
1. Grayscale conversion
2. Contrast normalization (histogram stretch or CLAHE)
3. Optional CLAHE (adaptive histogram equalization)
4. Working-resolution resize (preserve coordinate scale mapping)
5. Optional mild noise handling (Gaussian blur, light)

**Coordinate tracking:**
```python
scale_x = original_width / working_width
scale_y = original_height / working_height
```

Every keypoint in working space must be mappable back to original space.

**Acceptance:**
- [ ] Output is grayscale uint8 or float32
- [ ] Scale factors returned alongside image
- [ ] Does NOT claim to remove Sun angle

---

## B5 — SIFT 🔴 MUST

**File:** `backend/pipeline/sift.py`

**Input:** preprocessed grayscale image (working resolution)

**Output:**
```python
{
    "keypoints": list[cv2.KeyPoint],
    "descriptors": np.ndarray,      # float32, N×128
    "count": int
}
```

**Acceptance:**
- [ ] Returns keypoints and descriptors
- [ ] Count > 0 on real lunar image
- [ ] Works on both source and reference independently

---

## B6 — Matching 🔴 MUST

**File:** `backend/pipeline/matcher.py`

**Method:** BFMatcher (L2) or FLANN

**Steps:**
1. kNN matching (k=2)
2. Lowe ratio test (default threshold: 0.75)
3. Optional mutual consistency check

**Output:**
```python
{
    "tentative": int,
    "filtered": int,
    "src_pts": np.ndarray,    # Nx2, float32
    "dst_pts": np.ndarray,    # Nx2, float32
    "lowe_ratio": float
}
```

**Acceptance:**
- [ ] Lowe ratio threshold is configurable
- [ ] src_pts and dst_pts are aligned (same N)
- [ ] Returns all three count stages

---

## B7 — RANSAC Homography 🔴 MUST

**File:** `backend/pipeline/ransac.py`

**Input:** filtered src_pts, dst_pts

**Method:** `cv2.findHomography` with RANSAC

**Output:**
```python
{
    "matrix": np.ndarray,          # 3×3 float64
    "inlier_mask": np.ndarray,     # Nx1 uint8
    "inliers": int,
    "inlier_ratio": float,
    "reprojection_errors": np.ndarray,   # per-inlier px error
    "reprojection": {
        "mean_px": float,
        "median_px": float,
        "rmse_px": float,
        "p95_px": float
    }
}
```

**Acceptance:**
- [ ] Matrix is a valid 3×3 homography
- [ ] Reprojection errors computed for inliers only
- [ ] Returns all 4 reprojection statistics

---

## B8 — Registration 🔴 MUST

**File:** `backend/pipeline/registration.py`

**Input:** source image (original resolution), 3×3 homography matrix, reference image dimensions

**Operations:**
1. `cv2.warpPerspective` source → reference frame
2. Generate overlay-ready composite
3. Save before_after.png

**Output:**
```python
{
    "registered": np.ndarray,   # registered source image
    "overlay": np.ndarray,      # 50/50 blend with reference
    "status": "SUCCESS"
}
```

**Acceptance:**
- [ ] Registered image has same dims as reference
- [ ] Overlay is visually meaningful
- [ ] Status is one of: SUCCESS / FAILURE

---

## B9 — Synthetic Validation 🔴 MUST

**File:** `backend/validation/synthetic.py`

**Purpose:** Prove pipeline implementation correctness with known transforms.

**Process:**
1. Apply known transform T to real image → synthetic target
2. Run full pipeline on (image, synthetic_target)
3. Compare recovered homography H to T
4. Report coordinate recovery error

**Transforms to test (from `ground_truth/validation/synthetic_gt.csv`):**
- Translation only
- Rotation only
- Scale only
- Rotation + scale
- Mild perspective

**Output:**
```python
{
    "transform_type": str,
    "known_matrix": list,
    "recovered_matrix": list,
    "mean_recovery_error_px": float,
    "rmse_recovery_px": float,
    "success": bool
}
```

**Acceptance:**
- [ ] 5 transform types tested
- [ ] Recovery error < 1.0 px for translation/rotation
- [ ] Results logged to progress.md

---

## B10 — Serialization 🔴 MUST

**File:** `backend/pipeline/runner.py` (output section)

**Produce:**
```
artifacts/
├── registered.png
├── before_after.png
├── matches.csv
├── metrics.json
├── transformation.json
└── result.json
```

`result.json` must exactly match `contracts/result.schema.json`.

**Acceptance:**
- [ ] result.json validates against schema
- [ ] All artifact files written successfully
- [ ] Artifact paths returned in result.json

---

## B11 — API Server 🔴 MUST

**File:** `backend/api/server.py`

**Endpoints:**

```
GET  /health
     → {"status": "ok", "version": "0.1"}

GET  /pairs
     → [{"pair_id": "pair_001", "ohrc": "...", "tmc2": "..."}, ...]

POST /register
     body: {"pair_id": "pair_001"}
     → result.json (full schema)

GET  /results/{id}
     → cached result.json for run id

GET  /results/{id}/artifact/{name}
     → file download (registered.png / matches.csv / etc)
```

**Acceptance:**
- [ ] /health returns 200 without pipeline running
- [ ] /register triggers full pipeline
- [ ] /results returns valid schema
- [ ] Artifacts downloadable

---

## B12 — Ground-Truth Validation 🟡 SHOULD

**File:** `backend/validation/ground_truth.py`

**Input:**
```
ground_truth/control_points/pair_NNN.csv
```

**Process:**
1. For each control point: source_x, source_y → apply H → predicted reference_x, reference_y
2. Compare against reference_x, reference_y (where available)
3. Compute mean/median/RMSE/P95 error

**Critical rule:** Control points must NOT be used to fit the homography.

**Output:**
```python
{
    "ground_truth_type": "DERIVED_CORRESPONDENCE",
    "points": int,
    "mean_error_px": float | None,
    "median_error_px": float | None,
    "rmse_px": float | None,
    "p95_error_px": float | None,
    "spatial_coverage": float | None,
    "status": "REFERENCE_LIMITED"   # for derived CPs
}
```

**Note:** All 612 CPs have `reference_x = UNKNOWN` until PRADAN images are downloaded.
Status will be `REFERENCE_LIMITED` for all pairs except pair_012.

**Acceptance:**
- [ ] Does not crash on UNKNOWN reference coords
- [ ] Returns REFERENCE_LIMITED status when coords unavailable
- [ ] Does not use CPs in homography fitting

---

## Test Coverage

| Module | Test file | Minimum tests |
|--------|-----------|--------------|
| loader.py | test_loader.py | Load TIFF, correct dims |
| sift.py | test_sift.py | Non-zero keypoints |
| matcher.py | test_matcher.py | Lowe ratio, aligned output |
| ransac.py | test_ransac.py | Valid 3×3 matrix, inlier count |
| registration.py | test_registration.py | Correct output dims |
| synthetic.py | test_validation.py | 5 transform types |

---

## Priority if Time Runs Out

```
MUST: B1 B2 B4 B5 B6 B7 B8 B9 B10 B11
SHOULD: B3 B12
NICE: Extended test coverage
```

---

*Last updated: 2026-08-31*
