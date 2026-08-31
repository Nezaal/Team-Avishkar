# SIH26166 Frontend — Component Task Plan

> **Priority:** 🔴 MUST | 🟡 SHOULD | 🟢 NICE  
> **Stack:** Python / Streamlit  
> **Entry point:** `frontend/app/main.py`

---

## Pre-Work: Contract First

Before writing any frontend code, confirm `contracts/example_result.json` exists.

Copy it to `frontend/mock/result.json`.

All component development is against this schema.

---

## F1 — Skeleton 🔴 MUST

**Create directory structure:**

```
frontend/
├── app/main.py
├── components/
├── mock/result.json
├── assets/
└── README.md
```

**Acceptance:**
- [ ] `streamlit run frontend/app/main.py` starts without error
- [ ] Mock result.json loads
- [ ] Page title and layout skeleton visible

---

## F2 — Mock Mode 🔴 MUST

**Load pipeline:**

```python
# Priority order:
# 1. Live API response (when backend available)
# 2. frontend/mock/result.json (default during development)

import json
with open("frontend/mock/result.json") as f:
    result = json.load(f)
```

**Acceptance:**
- [ ] Runs fully without any backend connection
- [ ] Controlled by a config flag or env variable

---

## F3 — Image Pair Preview 🔴 MUST

**Display:**
- OHRC image (or placeholder)
- TMC-2 image (or placeholder)
- Filename, sensor, dimensions, resolution
- Correspondence lines overlay (inliers highlighted)
- Pair selectors (source + reference dropdowns)
- "Run Registration" button

**Acceptance:**
- [ ] Two image cards side by side
- [ ] Metadata labels visible
- [ ] Selectors functional (from mock pair list)
- [ ] Button triggers registration (or shows mock result)

---

## F4 — Registration Result 🔴 MUST

**Display:**
- Before image (original OHRC)
- After image (registered output)
- Overlay mode or blink comparison
- Slider (if practical in Streamlit)
- Registration status badge

**Acceptance:**
- [ ] Before/after visible
- [ ] Status badge shows SUCCESS / FAILURE / LOW_CONFIDENCE
- [ ] Images aligned correctly in overlay mode

---

## F5 — Correspondence Visualization 🔴 MUST

**Display:**
- Source image with keypoints plotted
- Reference image with keypoints plotted
- Lines connecting matched pairs
- Inliers (green) vs outliers (red)
- Match counts in legend

**Acceptance:**
- [ ] Lines visible on mock data
- [ ] Inlier/outlier color distinction
- [ ] Point count in UI

---

## F6 — Metrics Cards 🔴 MUST

**Display (Match Quality section):**

| Metric | Source |
|--------|--------|
| Features (source) | `matching.features_source` |
| Features (reference) | `matching.features_reference` |
| Tentative matches | `matching.tentative` |
| Filtered matches | `matching.filtered` |
| RANSAC inliers | `matching.inliers` |
| Inlier ratio | `matching.inlier_ratio` |

**Display (Geometric Consistency section):**

| Metric | Source |
|--------|--------|
| Mean reprojection error | `geometry.reprojection.mean_px` |
| Median reprojection error | `geometry.reprojection.median_px` |
| RMSE | `geometry.reprojection.rmse_px` |
| 95th percentile | `geometry.reprojection.p95_px` |

> ⚠️ Label this section "Transformation Self-Consistency" — not "accuracy".

**Acceptance:**
- [ ] All 10 metrics displayed
- [ ] Two sections clearly labeled

---

## F7 — Transformation Panel 🔴 MUST

**Display:**
- Model name (Homography)
- 3×3 matrix (formatted table)
- Inlier count
- Inlier ratio
- Reprojection statistics

**Acceptance:**
- [ ] Matrix formatted as table with 4 decimal places
- [ ] Model name and stats visible

---

## F8 — Ground-Truth Validation Panel 🔴 MUST

**This is a SEPARATE panel from F6. Must NEVER be merged with reprojection error.**

**Display:**

| Field | Source |
|-------|--------|
| Reference type | `validation.ground_truth_type` |
| Reference source | Derived from type |
| Control point count | `validation.points` |
| Mean error (px) | `validation.mean_error_px` |
| Median error (px) | `validation.median_error_px` |
| RMSE (px) | `validation.rmse_px` |
| 95th percentile | `validation.p95_error_px` |
| Spatial coverage | `validation.spatial_coverage` |
| Validation status | `validation.status` |

**Status labels:**
- `SUCCESS` → green badge
- `SUCCESS_WITHOUT_INDEPENDENT_VALIDATION` → yellow badge
- `LOW_CONFIDENCE` → orange badge
- `REFERENCE_LIMITED` → grey badge
- `FAILURE` → red badge

**Acceptance:**
- [ ] Panel is visually distinct from reprojection section
- [ ] Null values displayed as "N/A — reference limited"
- [ ] Status badge color-coded

---

## F9 — Reprojection Error Histogram 🟡 SHOULD

**Display:**
- Bar histogram of per-point reprojection errors
- Threshold line at 1.0 px
- Mean and median markers

**Acceptance:**
- [ ] Histogram renders from mock data
- [ ] Threshold line visible

---

## F10 — Correspondence Distribution Plot 🟡 SHOULD

**Display:**
- Scatter plot on source image coordinate space
- One dot per inlier
- Grid coverage overlay (optional)

**Acceptance:**
- [ ] Plot renders from mock data
- [ ] Labeled axes

---

## F11 — Export Controls 🟡 SHOULD

**Expose download links/buttons for:**
- Registered image (PNG)
- Matches CSV
- Metrics JSON
- Transformation JSON
- Validation report

**Acceptance:**
- [ ] Download buttons functional
- [ ] Files served from backend artifact URLs or local mock files

---

## F12 — API Integration 🔴 MUST (final step)

**Replace:**
```python
# Before
with open("frontend/mock/result.json") as f:
    result = json.load(f)
```

**With:**
```python
# After
import requests
result = requests.post("http://localhost:8000/register", json={"pair_id": pair_id}).json()
```

**Acceptance:**
- [ ] Frontend reads live backend response
- [ ] No UI redesign required
- [ ] Mock mode still works when API unavailable

---

## Integration Test Checklist

```
[ ] Select OHRC + TMC-2 pair
[ ] Click Run Registration
[ ] Correspondence lines appear
[ ] Before/after images appear
[ ] Metrics panel updates
[ ] Transformation panel updates
[ ] Ground-truth panel updates (separate)
[ ] Export controls functional
[ ] Mock mode works independently
[ ] Failure state renders correctly
```

---

*Last updated: 2026-08-31*
