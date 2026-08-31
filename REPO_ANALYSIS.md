# SIH26166 — Repository Analysis & Project Status

> **Project:** Chandrayaan-2 Autonomous Image Correspondence MVP (SIH26166)
> **Team:** Team Avishkar | **Reviewed:** 2026-08-31

---

## ✅ Are We on the Right Track?

**YES — solidly on the right track.**

Planning is professional-grade, scientifically honest, and correctly scoped.
The ground-truth dataset is complete. The parallel frontend/backend architecture is the right call.
The immediate blocker is that `frontend/`, `backend/`, and `contracts/` do not exist yet.

---

## 📁 Current Repo State

```
Team-Avishkar/
├── AGENT.md                    ✅ Master agent protocol
├── flow.md                     ✅ Current architecture map
├── progress.md                 ✅ Dev history (Entry 001 done)
├── technical-questions.md      ✅ 3 open, 3 resolved questions
├── doc/                        ✅ Master documentation folder
│   ├── README.md               ✅ NEW — master doc index
│   ├── SIH26166_MVP_PLAN.md    ✅ 15-hour parallel plan
│   ├── SIH26166_MVP_PRD_PARALLEL.md  ✅ PRD
│   ├── SIH26166_MVP_SRS_PARALLEL.md  ✅ SRS
│   ├── frontend/               ✅ NEW — frontend doc folder
│   │   ├── README.md
│   │   ├── FRONTEND_PLAN.md
│   │   ├── FRONTEND_AGENT.md
│   │   └── MOCK_DATA_GUIDE.md
│   └── backend/                ✅ NEW — backend doc folder
│       ├── README.md
│       ├── BACKEND_PLAN.md
│       ├── BACKEND_AGENT.md
│       └── API_CONTRACT.md
├── ground_truth/               ✅ Complete dataset (20 pairs, 612 CPs)
│   └── TASKS.md                ✅ NEW — ground truth task list
├── contracts/                  ❌ NOT CREATED YET
├── frontend/                   ❌ NOT CREATED YET
└── backend/                    ❌ NOT CREATED YET
```

---

## 🟢 What's Going Well

| Area | Status |
|------|--------|
| Ground truth dataset | ✅ 20 pairs, 612 derived CPs, 1 LOLA-independent pair |
| Scientific honesty | ✅ Zero fabricated CPs, clear disclaimers |
| Architecture planning | ✅ Frontend/backend split with shared contract |
| Documentation system | ✅ AGENT.md + 3 living files + separate frontend/backend docs |
| API contract | ✅ Fully designed in `doc/backend/API_CONTRACT.md` |
| SRS + PRD | ✅ Both well-scoped and coherent |
| MVP scope control | ✅ RIFT2/LoFTR/LLM/cloud explicitly excluded |

---

## 🔴 Blockers

| Blocker | Impact | Resolution |
|---------|--------|-----------|
| No PRADAN image access | Cannot do pixel-level validation | Get PRADAN login; see `ground_truth/TASKS.md` |
| TMC-2 dims unknown | reference_x/reference_y = UNKNOWN for all pairs | Download any TMC-2 image to read header dims |
| Zero pixel correspondences | No sub-pixel accuracy claims possible | Manual annotation for pairs A/B/C |
| `contracts/` not created | Frontend + backend cannot start in parallel | **Create this first** |
| `frontend/` not created | Dashboard missing | Start after contracts |
| `backend/` not created | CV pipeline missing | Start after contracts |

---

## 🏗️ Task Division

### FRONTEND (Streamlit Dashboard)

| # | Task | Priority |
|---|------|----------|
| F1 | Create `frontend/` skeleton (app/, components/, mock/, assets/) | 🔴 MUST |
| F2 | Mock mode — load result.json without backend | 🔴 MUST |
| F3 | Image pair preview — OHRC + TMC-2 cards, selectors, Run button | 🔴 MUST |
| F4 | Registration result — before/after, overlay, status badge | 🔴 MUST |
| F5 | Correspondence visualization — colored lines, inlier/outlier | 🔴 MUST |
| F6 | Metrics cards — features, matches, inliers, inlier ratio | 🔴 MUST |
| F7 | Transformation panel — model, 3×3 matrix, reprojection stats | 🔴 MUST |
| F8 | Ground-truth panel — SEPARATE from reprojection, null-safe | 🔴 MUST |
| F9 | Reprojection error histogram | 🟡 SHOULD |
| F10 | Correspondence distribution scatter plot | 🟡 SHOULD |
| F11 | Export controls — download buttons for all artifacts | 🟡 SHOULD |
| F12 | API integration — replace mock with live backend response | 🔴 MUST (final) |

### BACKEND (CV Pipeline + API)

| # | Task | Priority |
|---|------|----------|
| B1 | Create `backend/` skeleton (api/, pipeline/, validation/, tests/) | 🔴 MUST |
| B2 | Image loader — TIFF/IMG → array + dims + metadata | 🔴 MUST |
| B3 | Pair analyzer — resolution ratio, contrast, texture, working scale | 🟡 SHOULD |
| B4 | Preprocessing — grayscale, normalization, CLAHE, resize + scale map | 🔴 MUST |
| B5 | SIFT — keypoints + descriptors for both images | 🔴 MUST |
| B6 | Matching — BFMatcher/FLANN + Lowe ratio + mutual consistency | 🔴 MUST |
| B7 | RANSAC — homography + inlier mask + reprojection errors | 🔴 MUST |
| B8 | Registration — warpPerspective + overlay composite | 🔴 MUST |
| B9 | Synthetic validation — 5 known transforms from synthetic_gt.csv | 🔴 MUST |
| B10 | Serialization — result.json + all artifacts matching contract | 🔴 MUST |
| B11 | API server — /health /pairs /register /results/{id} | 🔴 MUST |
| B12 | Ground-truth validation — CP coords → error metrics | 🟡 SHOULD |

### SHARED (contracts/)

| # | Task | Priority |
|---|------|----------|
| C1 | `contracts/result.schema.json` — JSON schema definition | 🔴 MUST FIRST |
| C2 | `contracts/example_result.json` — full example response | 🔴 MUST FIRST |

### GROUND TRUTH (ground_truth/)

See `ground_truth/TASKS.md` for the complete task list.
Short version: PRADAN login → download images → run IIT overlap script → manual annotation.

---

## 📋 Recommended Build Order

```
Step 1  → contracts/result.schema.json + example_result.json    ← TODAY FIRST
Step 2  → frontend/ skeleton + F2 mock mode
Step 3  → backend/ skeleton + B2 image loader + B5 SIFT
Step 4  → F3 F4 (image preview + registration result panels)
Step 5  → B6 B7 B8 (matching + RANSAC + registration)
Step 6  → F5 F6 F7 (correspondence viz + metrics + transform)
Step 7  → B9 B10 B11 (synthetic validation + serialization + API)
Step 8  → F8 F9 (GT panel + histogram)
Step 9  → F12 API integration (frontend reads live backend)
Step 10 → End-to-end test: pairs 001, 012, 003
Step 11 → Stabilize demo, export, screenshots, judge evidence
```

---

## 🧠 Scientific Integrity — Key Rules

| Rule | Explanation |
|------|------------|
| Reprojection error ≠ accuracy | Label it "Transformation Self-Consistency" |
| 612 CPs are NOT manually verified | Display as "geospatially_derived" |
| Only pair_012 has LOLA independence | Do not claim independence for others |
| Synthetic validation ≠ real accuracy | Only proves implementation correctness |
| null GT errors → "N/A — reference limited" | Never display as 0.0 |

> **For judges:** The ground-truth dataset is scientifically honest. This distinguishes Team Avishkar from teams that fabricate accuracy numbers.

---

*Generated: 2026-08-31 | Team Avishkar — SIH26166*
