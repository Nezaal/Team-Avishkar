# SIH26166 Frontend Documentation

> **Workstream:** Frontend — Dashboard & Visualization  
> **Stack:** Python / Streamlit  
> **Dependency:** Contracts only — must work without backend via mock mode

---

## Ownership

The frontend team owns **everything** inside `frontend/`.

| Owns | Does NOT own |
|------|-------------|
| Dashboard layout | SIFT / feature detection |
| Image pair preview | Matching / RANSAC |
| Source/reference selectors | Homography estimation |
| Correspondence visualization | Image registration / warping |
| Before/after comparison | Ground-truth computation |
| Overlay / blink / slider | CV preprocessing |
| Reprojection histogram | Coordinate system math |
| Metrics cards | Backend state management |
| Transformation summary | API server logic |
| Ground-truth validation panel | |
| Status / confidence display | |
| Export / download controls | |
| Mock-data mode | |
| API response rendering | |

---

## Directory Structure (to be created)

```
frontend/
├── app/
│   └── main.py                 ← Streamlit entry point
├── components/
│   ├── image_pair_preview.py   ← F3: Image pair cards + selectors
│   ├── registration_result.py  ← F4: Before/after + overlay
│   ├── correspondence_viz.py   ← F5: Correspondence line plots
│   ├── metrics_cards.py        ← F6: Match quality metrics
│   ├── transformation_panel.py ← F7: Homography matrix display
│   ├── validation_panel.py     ← F8: Ground-truth validation (SEPARATE)
│   ├── reprojection_hist.py    ← F9: Error distribution histogram
│   ├── distribution_plot.py    ← F10: Correspondence scatter
│   └── export_controls.py      ← F11: Download buttons
├── mock/
│   └── result.json             ← Example backend response (from contracts/)
├── assets/
│   └── mock_ohrc.png           ← Placeholder lunar images
└── README.md                   ← This file
```

---

## Mock-First Principle

The frontend **must be runnable without the backend**.

Load data from:
```
frontend/mock/result.json
```

This file mirrors `contracts/example_result.json`.

When the backend API is ready, replace the mock load with an HTTP request.
**Do not redesign the UI during API integration.**

---

## Key Scientific Rule for the Dashboard

The UI **must visually distinguish** three separate categories:

```
MATCH QUALITY           → feature count, tentative, filtered, inliers, inlier ratio
GEOMETRIC CONSISTENCY   → reprojection error (self-consistency, NOT accuracy)
GROUND-TRUTH ACCURACY   → independent control-point error (separate panel)
```

> ⚠️ Never label reprojection error as "accuracy" or "ground-truth error".

---

## Component Tasks

See `FRONTEND_PLAN.md` for the full task list with priorities and acceptance criteria.

---

## Integration with Backend

The frontend communicates with the backend **only** through:

1. `GET /results/{id}` → result JSON matching `contracts/result.schema.json`
2. `GET /results/{id}/artifact/{name}` → image/CSV artifacts

The frontend must not import any backend Python module directly.

---

## Documents in This Folder

| File | Purpose |
|------|---------|
| `README.md` | This file — overview and ownership |
| `FRONTEND_PLAN.md` | Detailed component task list with priorities |
| `FRONTEND_AGENT.md` | Developer/agent protocol for frontend work |
| `MOCK_DATA_GUIDE.md` | How to use, extend, and update mock data |

---

*Last updated: 2026-08-31*
