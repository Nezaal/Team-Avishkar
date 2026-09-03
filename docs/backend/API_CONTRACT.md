# SIH26166 Backend — API Contract

> **Version:** 1.0  
> **Status:** Draft — must be agreed before parallel implementation begins  
> **Owner:** Backend team (schema only — frontend reads it)

---

## Endpoints

### GET /health

```
Response 200:
{
  "status": "ok",
  "version": "0.1"
}
```

### GET /pairs

```
Response 200:
[
  {
    "pair_id": "pair_001",
    "ohrc_id": "20200825T1127278043",
    "tmc2_id": "provisional_tmc2_41E",
    "region": "South_Polar_41E",
    "quality": "B",
    "has_control_points": true,
    "independent_reference": false
  },
  ...
]
```

### POST /register

```
Request body:
{
  "pair_id": "pair_001"
}

Response 200: <full result JSON (see schema below)>
Response 422: {"error": "pair not found"}
Response 500: {"error": "pipeline failed", "detail": "..."}
```

### GET /results/{id}

```
Response 200: <full result JSON>
Response 404: {"error": "result not found"}
```

### GET /results/{id}/artifact/{name}

```
name options: registered.png | before_after.png | matches.csv | metrics.json | transformation.json

Response 200: file download
Response 404: {"error": "artifact not found"}
```

---

## Full Result JSON Schema

```json
{
  "pair": {
    "source": {
      "sensor": "OHRC",
      "name": "string",
      "width": 0,
      "height": 0,
      "resolution_m": 0.0
    },
    "reference": {
      "sensor": "TMC-2",
      "name": "string",
      "width": 0,
      "height": 0,
      "resolution_m": 0.0
    }
  },
  "preprocessing": {
    "operations": ["grayscale", "contrast_normalization"],
    "parameters": {
      "working_scale": 1.0,
      "clahe_clip": 2.0,
      "scale_x": 1.0,
      "scale_y": 1.0
    }
  },
  "matching": {
    "features_source": 0,
    "features_reference": 0,
    "tentative": 0,
    "filtered": 0,
    "inliers": 0,
    "inlier_ratio": 0.0
  },
  "geometry": {
    "model": "Homography",
    "matrix": [
      [1.0, 0.0, 0.0],
      [0.0, 1.0, 0.0],
      [0.0, 0.0, 1.0]
    ],
    "reprojection": {
      "mean_px": 0.0,
      "median_px": 0.0,
      "rmse_px": 0.0,
      "p95_px": 0.0
    }
  },
  "registration": {
    "status": "SUCCESS",
    "registered_image": "artifacts/registered.png"
  },
  "validation": {
    "ground_truth_type": "DERIVED_CORRESPONDENCE",
    "reference_source": "IIT CSV geospatially derived",
    "points": 0,
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
    "message": "string"
  }
}
```

---

## Status Levels

| Level | Meaning |
|-------|---------|
| `SUCCESS` | Pipeline ran, independent validation passed |
| `SUCCESS_WITHOUT_INDEPENDENT_VALIDATION` | Pipeline ran, no independent GT available |
| `LOW_CONFIDENCE` | Too few inliers or poor reprojection |
| `REFERENCE_LIMITED` | Ran but CP reference coords unavailable |
| `FAILURE` | Pipeline failed or homography degenerate |

---

## Validation Status Levels

| Status | Meaning |
|--------|---------|
| `PASSED` | GT error below threshold |
| `REFERENCE_LIMITED` | No reference pixel coords (most pairs) |
| `DERIVED_ONLY` | Only derived CPs, not independently verified |
| `SYNTHETIC_ONLY` | Only synthetic validation ran |
| `FAILED` | GT error above threshold |

---

## Schema Change Protocol

If the schema needs to change:

1. Backend proposes the change in `progress.md`
2. Frontend confirms compatibility
3. Update `contracts/result.schema.json`
4. Update `contracts/example_result.json`
5. Update `frontend/mock/result.json`
6. Record change in `progress.md` and `flow.md`

---

## matches.csv Schema

```
src_x,src_y,dst_x,dst_y,is_inlier,reprojection_error_px
1024.3,897.1,512.7,448.2,1,0.34
...
```

## metrics.json Schema

```json
{
  "features_source": 18642,
  "features_reference": 12000,
  "tentative": 8000,
  "filtered": 5000,
  "inliers": 3274,
  "inlier_ratio": 0.655,
  "reprojection_mean_px": 0.38,
  "reprojection_median_px": 0.34,
  "reprojection_rmse_px": 0.47,
  "reprojection_p95_px": 0.91
}
```

## transformation.json Schema

```json
{
  "model": "Homography",
  "matrix": [
    [0.9987, -0.0482, 15.2371],
    [0.0469, 0.9989, -11.4827],
    [0.000001, 0.000002, 1.0]
  ],
  "coordinate_system": "working_resolution",
  "scale_x": 0.5,
  "scale_y": 0.5
}
```

---

*Last updated: 2026-08-31*
