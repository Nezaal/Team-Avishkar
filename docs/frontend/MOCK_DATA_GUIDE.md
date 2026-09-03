# SIH26166 Frontend — Mock Data Guide

## Purpose

The mock data allows the frontend to be developed and tested without a running backend.

---

## Source of Truth

The authoritative schema lives at:
```
contracts/result.schema.json
contracts/example_result.json
```

The frontend copy lives at:
```
frontend/mock/result.json
```

When the contracts are updated, copy `example_result.json` to `frontend/mock/result.json`.

---

## Loading Mock Data

```python
import json
import os

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

def load_result(pair_id=None):
    if MOCK_MODE:
        with open("frontend/mock/result.json") as f:
            return json.load(f)
    else:
        import requests
        return requests.post(
            "http://localhost:8000/register",
            json={"pair_id": pair_id}
        ).json()
```

---

## Mock Result Schema

The mock result must match this structure exactly:

```json
{
  "pair": {
    "source": {
      "sensor": "OHRC",
      "name": "ohrc_demo.tif",
      "width": 2048,
      "height": 2048,
      "resolution_m": 0.25
    },
    "reference": {
      "sensor": "TMC-2",
      "name": "tmc2_demo.tif",
      "width": 1024,
      "height": 1024,
      "resolution_m": 5.0
    }
  },
  "preprocessing": {
    "operations": ["grayscale", "contrast_normalization", "CLAHE"],
    "parameters": {
      "working_scale": 0.5,
      "clahe_clip": 2.0
    }
  },
  "matching": {
    "features_source": 18642,
    "features_reference": 12000,
    "tentative": 8000,
    "filtered": 5000,
    "inliers": 3274,
    "inlier_ratio": 0.655
  },
  "geometry": {
    "model": "Homography",
    "matrix": [
      [0.9987, -0.0482, 15.2371],
      [0.0469,  0.9989, -11.4827],
      [0.000001, 0.000002, 1.0]
    ],
    "reprojection": {
      "mean_px": 0.38,
      "median_px": 0.34,
      "rmse_px": 0.47,
      "p95_px": 0.91
    }
  },
  "registration": {
    "status": "SUCCESS",
    "registered_image": "artifacts/registered.png"
  },
  "validation": {
    "ground_truth_type": "GEOREFERENCED_REFERENCE",
    "points": 36,
    "mean_error_px": null,
    "median_error_px": null,
    "rmse_px": null,
    "p95_error_px": null,
    "spatial_coverage": null,
    "status": "REFERENCE_LIMITED"
  },
  "artifacts": {
    "matches": "artifacts/matches.csv",
    "metrics": "artifacts/metrics.json",
    "transformation": "artifacts/transformation.json",
    "registered_image": "artifacts/registered.png",
    "before_after": "artifacts/before_after.png"
  },
  "status": {
    "level": "SUCCESS_WITHOUT_INDEPENDENT_VALIDATION",
    "message": "Registration completed. Reprojection error is self-consistency only, not ground-truth accuracy."
  }
}
```

---

## What to Display When Values Are null

| Field | null display |
|-------|-------------|
| `mean_error_px` | "N/A — reference limited" |
| `median_error_px` | "N/A — reference limited" |
| `rmse_px` | "N/A — reference limited" |
| `p95_error_px` | "N/A — reference limited" |
| `spatial_coverage` | "N/A" |

> ⚠️ Never display null as 0.0 — that would imply perfect accuracy.

---

## Extending Mock Data

To test different status scenarios, create additional mock files:

```
frontend/mock/result_success.json
frontend/mock/result_low_confidence.json
frontend/mock/result_failure.json
```

Add a selector in the UI for test mode switching.

---

*Last updated: 2026-08-31*
