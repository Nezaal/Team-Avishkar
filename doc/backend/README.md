# SIH26166 Backend Documentation

> **Workstream:** Backend — CV Pipeline, Validation & API  
> **Stack:** Python, OpenCV, NumPy, FastAPI (or Flask)  
> **Dependency:** Contracts only — must run without a connected frontend

---

## Ownership

The backend team owns **everything** inside `backend/`.

| Owns | Does NOT own |
|------|-------------|
| Image loading (TIFF, IMG) | Dashboard layout |
| Metadata inspection | Visual styling |
| Pair analysis | Frontend state management |
| Preprocessing (grayscale, CLAHE, resize) | Presentation logic |
| SIFT feature extraction | API client logic |
| Descriptor matching (BFMatcher/FLANN) | |
| Lowe ratio filtering | |
| RANSAC homography estimation | |
| Registration / warping | |
| Reprojection metrics | |
| Ground-truth validation | |
| Synthetic validation | |
| Result serialization | |
| API server | |
| Artifact generation | |

---

## Directory Structure (to be created)

```
backend/
├── api/
│   └── server.py               ← FastAPI/Flask server
├── pipeline/
│   ├── loader.py               ← B2: Image loading
│   ├── pair_analyzer.py        ← B3: Pair analysis
│   ├── preprocessor.py         ← B4: Preprocessing
│   ├── sift.py                 ← B5: SIFT extraction
│   ├── matcher.py              ← B6: Descriptor matching
│   ├── ransac.py               ← B7: RANSAC homography
│   ├── registration.py         ← B8: Image warping
│   └── runner.py               ← Pipeline orchestrator
├── validation/
│   ├── ground_truth.py         ← B12: GT validation
│   └── synthetic.py            ← B9: Synthetic validation
├── models/
│   └── result.py               ← Result data classes
├── tests/
│   ├── test_sift.py
│   ├── test_ransac.py
│   ├── test_registration.py
│   └── test_validation.py
└── README.md                   ← This file
```

---

## API Endpoints (minimum)

```
GET  /health                          → {status: ok}
GET  /pairs                           → list of available pairs
POST /register                        → run pipeline on pair
GET  /results/{id}                    → result JSON
GET  /results/{id}/artifact/{name}    → registered image / CSV / JSON
```

See `API_CONTRACT.md` for full schema.

---

## Pipeline Steps

```
Input (OHRC + TMC-2 images)
    ↓
Pair Analysis (dimensions, scale diff, contrast, texture)
    ↓
Preprocessing (grayscale, normalization, CLAHE, resize)
    ↓
SIFT (keypoints + descriptors for both images)
    ↓
Matching (BFMatcher/FLANN + Lowe ratio)
    ↓
RANSAC (homography + inlier mask)
    ↓
Registration (warp source → reference coords)
    ↓
Metrics (reprojection error, spatial coverage)
    ↓
Validation (synthetic + ground-truth control points)
    ↓
Serialization (result.json + artifacts)
    ↓
API Response
```

---

## Critical Rules

1. **Never use ground-truth control points to fit the homography.** They are for evaluation only.
2. **Reprojection error ≠ ground-truth accuracy.** Label them separately in the result JSON.
3. **Coordinate tracking:** every resize must preserve scale mapping back to original resolution.
4. **Synthetic validation is for implementation correctness only** — not real lunar accuracy.

---

## Documents in This Folder

| File | Purpose |
|------|---------|
| `README.md` | This file — overview and ownership |
| `BACKEND_PLAN.md` | Detailed module task list with priorities |
| `BACKEND_AGENT.md` | Developer/agent protocol for backend work |
| `API_CONTRACT.md` | API endpoints and full result schema |

---

*Last updated: 2026-08-31*
