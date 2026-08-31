# flow.md — SIH26166 Current System Architecture

> **Rule:** This file reflects ONLY the merged, accepted architecture on `main`.
> Do NOT update this file from a feature branch.
> Only update after a branch is merged to `main` and the architecture has actually changed.
> Record the update in `progress.md` with the branch name.

---

## Last Updated

```
Date:     2026-08-31
Branch:   main
Author:   Antigravity (AI agent)
Entry:    progress.md Entry 002
```

---

## Current System Stage

**Data Engineering** — ground truth dataset built, CV pipeline not yet started.

```
[DONE]   Ground truth dataset (ground_truth/)
[DONE]   Documentation structure (doc/)
[DONE]   AGENT.md multi-branch protocol
[PENDING] contracts/ — result schema + example JSON
[PENDING] frontend/ — Streamlit dashboard
[PENDING] backend/  — CV pipeline + API
```

---

## Architecture Overview

```
                    ┌────────────────────┐
                    │      FRONTEND      │
                    │  Streamlit Dashboard│
                    │  (NOT BUILT YET)   │
                    └─────────┬──────────┘
                              │
                         HTTP / JSON
                              │
                    ┌─────────▼──────────┐
                    │       BACKEND      │
                    │      API Server    │
                    │  (NOT BUILT YET)   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │    CV Pipeline     │
                    │  (NOT BUILT YET)   │
                    ├────────────────────┤
                    │ Input/Metadata     │
                    │ Pair Analyzer      │
                    │ Preprocessing      │
                    │ SIFT               │
                    │ Matching           │
                    │ Filtering          │
                    │ RANSAC             │
                    │ Homography         │
                    │ Registration       │
                    │ Validation         │
                    └─────────┬──────────┘
                              │
                    Result JSON + artifacts
                              │
                    ┌─────────▼──────────┐
                    │      FRONTEND      │
                    │   Visual Evidence  │
                    │  (NOT BUILT YET)   │
                    └────────────────────┘
```

---

## Repository Directory Map (Current)

```
Team-Avishkar/
├── AGENT.md                   ← Master multi-branch agent protocol  [EXISTS]
├── flow.md                    ← This file — current architecture    [EXISTS]
├── progress.md                ← Development history                 [EXISTS]
├── technical-questions.md     ← Technical knowledge base            [EXISTS]
├── REPO_ANALYSIS.md           ← Project status overview             [EXISTS]
│
├── doc/                       ← Master documentation folder         [EXISTS]
│   ├── README.md
│   ├── SIH26166_MVP_PLAN.md
│   ├── SIH26166_MVP_PRD_PARALLEL.md
│   ├── SIH26166_MVP_SRS_PARALLEL.md
│   ├── frontend/              ← Frontend documentation              [EXISTS]
│   │   ├── README.md
│   │   ├── FRONTEND_PLAN.md
│   │   ├── FRONTEND_AGENT.md
│   │   └── MOCK_DATA_GUIDE.md
│   └── backend/               ← Backend documentation               [EXISTS]
│       ├── README.md
│       ├── BACKEND_PLAN.md
│       ├── BACKEND_AGENT.md
│       └── API_CONTRACT.md
│
├── ground_truth/              ← Reference dataset                   [EXISTS]
│   ├── README.md
│   ├── TASKS.md               ← Ground truth task list              [EXISTS]
│   ├── manifests/             ← pairs.csv, validation.csv
│   ├── pairs/                 ← pair_001 to pair_020 (metadata only)
│   ├── control_points/        ← 17 CSVs × 36 derived points = 612
│   ├── sources/               ← IIT CSVs + build_dataset.py
│   └── validation/            ← rejected.csv, synthetic_gt.csv
│
├── contracts/                 ← Shared API schema         [NOT CREATED YET]
│   ├── result.schema.json
│   └── example_result.json
│
├── frontend/                  ← Streamlit dashboard       [NOT CREATED YET]
│   ├── app/
│   ├── components/
│   ├── mock/
│   └── assets/
│
└── backend/                   ← CV pipeline + API         [NOT CREATED YET]
    ├── api/
    ├── pipeline/
    ├── validation/
    ├── models/
    └── tests/
```

---

## Data Flow (Designed, Not Yet Implemented)

```
OHRC .img  +  TMC-2 .img
        ↓
    Backend: pair analysis
        ↓
    Backend: preprocessing (grayscale, CLAHE, resize)
        ↓
    Backend: SIFT (keypoints + descriptors, both images)
        ↓
    Backend: matching (BFMatcher/FLANN + Lowe ratio)
        ↓
    Backend: RANSAC → homography + inlier mask
        ↓
    Backend: registration (warpPerspective)
        ↓
    Backend: metrics (reprojection error, spatial coverage)
        ↓
    Backend: validation (synthetic + ground-truth CPs)
        ↓
    Backend: serialization → result.json + artifacts
        ↓
    Backend API: POST /register → result JSON
        ↓
    Frontend: dashboard renders result
```

---

## Ground Truth State (Current)

```
Pairs:                20 (16 quality-B, 4 quality-C)
Control points:       612 (geospatially_derived only — NOT pixel-verified)
Independent refs:     1 (pair_012, LOLA/USGS)
Synthetic GT:         5 (exact known transforms)
Images downloaded:    0 (PRADAN login required)
TMC-2 dims known:     NO (all UNKNOWN)
Manual annotations:   0
```

---

## Interface Contract (Designed, Not Yet in contracts/ directory)

```json
{
  "pair": {},
  "preprocessing": {},
  "matching": {},
  "geometry": {},
  "registration": {},
  "validation": {},
  "artifacts": {},
  "status": {}
}
```

Full schema defined in `doc/backend/API_CONTRACT.md`.
`contracts/` directory must be created and agreed before parallel dev starts.

---

## Branch / Workstream Map

```
Branch prefix        Owns
──────────────────────────────────────────
frontend/*           frontend/
backend/*            backend/
ground_truth/*       ground_truth/
data/*               ground_truth/ (data download only)
fix/*                any (hotfixes)
```

`flow.md` is updated **only after merge to main**.

---

*This file must never contain planned or future architecture as if it exists.*
*It describes only what is currently merged and working on `main`.*
