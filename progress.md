# progress.md — SIH26166 Development History

> **Rule:** This file is APPEND-ONLY. Never delete or overwrite an existing entry.
> Every entry MUST include `Git branch:` and `Author/Agent:`.
> New entries go at the BOTTOM of this file.

---

## Entry 001 — Ground Truth Dataset Build

```
Date/time:       2026-08-31 (15:14–15:31 IST)
Git branch:      main
Author/Agent:    Antigravity (AI agent)
Workstream:      ground_truth
Change:          Built ground_truth/ dataset from scratch — data engineering only
Files/modules:   ground_truth/ (new directory tree, 60+ files)
```

### What Changed

Build the SIH26166 ground-truth dataset for the OHRC <-> TMC-2 image-registration MVP.
Data engineering task only — no CV pipeline code.

### Research Performed

#### 1. Project Documents Read
- AGENT.md, SIH26166_MVP_SRS.md, SIH26166_MVP_PRD.md
- Confirmed: OHRC/TMC-2 optical registration scope, ground-truth requirements (30-50 CPs/pair), MVP pair strategy (Pair A/B/C).

#### 2. IIT InterIIT Tech Meet 11.0 Repository (PRIMARY SOURCE)
- URL: https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0
- License: Apache-2.0

Files found and downloaded:
- coordinates_ohrc.csv (25 OHRC scenes, each with 4 corner lat/lon, image dimensions, pixel resolution)
- coordinates_tmc2.csv (1,083 TMC-2 orbital strip records, same schema)

IIT team facts:
- They scraped ISRO PRADAN portal for OHRC and TMC-2 images.
- Used Haversine-distance corner-containment test to identify overlapping pairs.
- Found 18 OHRC/TMC-2 overlapping patches from 6 unique TMC-2 scenes.
- Bilinearly interpolated OHRC corner coordinates into TMC-2 pixel space.
- Applied affine transforms to align the images.
- Their primary goal was ESRGAN super-resolution, not registration.
- Their coordinate mapping is reusable as DERIVED_CORRESPONDENCE ground truth.

OHRC scenes (all 25) span:
- South polar cluster (68-74 S, 20-44 E): majority of scenes
- Southern mid-latitude (61-66 S, 31-57 E): several scenes
- Mid-southern (12-21 S, 23-41 E): 2021 scenes
- Equatorial south (14-17 S, 69-71 E): 1 scene (2019)
- Western hemisphere polar (68-69 S, 341 E): 2021 scenes

#### 3. USGS / Ames Stereo Pipeline Documentation (SECONDARY SOURCE)
- URL: https://stereopipeline.readthedocs.io/en/latest/examples/chandrayaan2.html

Found explicit product IDs for south-polar ~20E example:
- OHRC: ch2_ohr_nrp_20200827T0030107497_d_img_d18
- OHRC: ch2_ohr_nrp_20200827T0226453039_d_img_d18
- TMC-2: ch2_tmc_ndn_20231101T0125121377_d_oth_d18
- TMC-2: ch2_tmc_ndn_20231101T0125121377_d_dtm_d18

USGS compares derived terrain against LOLA as independent reference.
These OHRC IDs match IIT CSV entries (cross-validated).

#### 4. LOLA as Independent Reference
- URL: https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
- Products: LDEM_60S_120M (120m/px), LDEM_75S (higher res)
- Independent of Chandrayaan-2.
- Used as independent reference for pair_012 only.

#### 5. ISRO PRADAN Portal
- URL: https://pradan.issdc.gov.in/ch2/
- Login required for all image pixel data.
- Corner coordinate metadata available via IIT CSV.
- Decision: proceed coordinate-only, document download instructions.

### How Control Points Were Derived

Process for all 612 control points (verification_method = geospatially_derived):

1. Extract OHRC 4-corner lat/lon from IIT CSV (confirmed real metadata).
2. Determine TMC-2 approximate bounding box from IIT methodology.
3. Compute geographic intersection of OHRC and TMC-2 footprints.
4. Place 6x6 = 36 grid points within the intersection.
5. For each grid point (lat, lon):
   - Bilinear interpolation using OHRC corners + image dimensions -> OHRC pixel (x, y).
   - TMC-2 pixel = UNKNOWN (image dimensions not in TMC-2 CSV).
6. Record with explicit verification_method = geospatially_derived.

This is NOT pixel-level ground truth. It is geographic reference derivable to
~pixel-width accuracy at OHRC resolution, but not independently verified.

### Files Created

```
ground_truth/
  README.md
  manifests/pairs.csv (20 pairs, all schema fields)
  manifests/validation.csv (20 rows, all classification fields)
  pairs/pair_001/ ... pair_020/ (metadata.json + README.md each)
  control_points/pair_001.csv ... pair_017 usable (36 pts each = 612 total)
  sources/coordinates_ohrc_iit.csv (downloaded raw)
  sources/coordinates_tmc2_iit.csv (downloaded raw)
  sources/build_dataset.py (reproducible builder)
  validation/rejected.csv (7 rejected candidates)
  validation/synthetic/synthetic_gt.csv (5 synthetic transform definitions)
```

### Result

SUCCESS

```
Pairs created:               20
OHRC+TMC-2 pairs:            20
Quality B pairs:             16
Quality C pairs:              4
Pairs with control points:   17
Total control points:        612
Points per pair (confirmed): 36 (6x6 grid)
Independent references:       1 (pair_012, LOLA via USGS/ASP)
Synthetic GT samples:         5
Rejected candidates:          7
```

Ground Truth Classification:
- DERIVED_CORRESPONDENCE:   19 pairs (corner coordinate interpolation, NOT independent)
- GEOREFERENCED_REFERENCE:   1 pair (pair_012, USGS-documented, LOLA independent reference)
- EXACT_SYNTHETIC_GT:        5 samples (synthetic_gt.csv, exact known transformations)

### Problems/Limitations

1. Images behind PRADAN login — pixel validation impossible without account.
2. TMC-2 image dimensions not in IIT CSV — TMC-2 pixel (x,y) CANNOT be computed.
3. IIT team did not publish the 6 exact TMC-2 product IDs used.
4. 4 pairs (015-018) have inferred overlap only — not confirmed by IIT overlap script.
5. Only 1 pair has external independent reference (LOLA).
6. Zero manually verified pixel correspondences in entire dataset.

### Next Step

1. PRADAN access -> download actual OHRC and TMC-2 image files for pairs 001, 005, 012.
2. Run IIT ohrc_tmc_overlap.py to recover exact TMC-2 product IDs for 6 TMC scenes.
3. Manual annotation: 30+ pixel correspondences for pairs 001 (Pair A), 005 (Pair B), 003 (Pair C).
4. LOLA download: clip LDEM_60S to 67-71 S, 19-22 E for pair_012 independent validation.
5. Once TMC-2 image dims known: re-run build_dataset.py to populate reference_x/reference_y.
6. Proceed to CV pipeline implementation (separate task).

---

## Entry 002 — Documentation Structure, Task Division & AGENT.md Multi-Branch Update

```
Date/time:       2026-08-31 (16:14–16:32 IST)
Git branch:      main
Author/Agent:    Antigravity (AI agent)
Workstream:      shared
Change:          Created doc/frontend/, doc/backend/, ground_truth/TASKS.md,
                 REPO_ANALYSIS.md, doc/README.md. Rewrote AGENT.md with
                 explicit multi-branch / multi-teammate conflict rules.
Files/modules:   AGENT.md, REPO_ANALYSIS.md, doc/README.md, doc/frontend/*,
                 doc/backend/*, ground_truth/TASKS.md
```

### What Changed

1. **AGENT.md** — fully rewritten to add:
   - Section 5: Multi-Branch / Multi-Teammate Rules (branch naming convention,
     `flow.md` as merge-gate, conflict resolution for all 3 living files,
     workstream ownership table, pre-PR checklist, contracts/ change protocol)
   - Section 12: Workstream Ownership Summary
   - Section 15: Quick Reference Card
   - Updated `progress.md` entry format to include `Workstream:` field
   - Updated `technical-questions.md` question format to include `Branch-raised:`
     and `Last-updated-by:` fields

2. **doc/README.md** — created master documentation index

3. **doc/frontend/** — created with 4 files:
   - README.md (ownership table)
   - FRONTEND_PLAN.md (F1–F12 tasks with acceptance criteria)
   - FRONTEND_AGENT.md (developer protocol)
   - MOCK_DATA_GUIDE.md (mock data schema + null display rules)

4. **doc/backend/** — created with 4 files:
   - README.md (ownership table)
   - BACKEND_PLAN.md (B1–B12 modules with I/O specs)
   - BACKEND_AGENT.md (developer protocol)
   - API_CONTRACT.md (all endpoints + full result JSON schema)

5. **ground_truth/TASKS.md** — created 10-task ground truth work plan
   (GT-00 through GT-10) with assignee types, dependencies, effort estimates

6. **REPO_ANALYSIS.md** — created root-level project status document

### Technical Impact

- All future progress.md entries MUST include `Git branch:` and `Author/Agent:`.
- `flow.md` must NOT be updated from feature branches — only after merge to main.
- Branch naming convention is now defined: frontend/* | backend/* | ground_truth/* | fix/*.
- Conflict resolution protocol is defined for all 3 living files.

### Validation

Files verified present:
- AGENT.md (rewritten, 15 sections)
- REPO_ANALYSIS.md (root level)
- doc/README.md
- doc/frontend/README.md, FRONTEND_PLAN.md, FRONTEND_AGENT.md, MOCK_DATA_GUIDE.md
- doc/backend/README.md, BACKEND_PLAN.md, BACKEND_AGENT.md, API_CONTRACT.md
- ground_truth/TASKS.md

### Result

SUCCESS

### Problems/Limitations

None. Pure documentation — no code changed.

### Next Step

1. Create `contracts/result.schema.json` and `contracts/example_result.json`.
2. Create Git branches: `frontend/dashboard-skeleton` and `backend/pipeline-skeleton`.
3. Assign GT-07 and GT-08 (no PRADAN needed) to a teammate immediately.

---

<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- NEW ENTRIES GO BELOW THIS LINE                                         -->
<!-- Format: ## Entry NNN — <title>                                         -->
<!-- MANDATORY FIELDS: Date/time, Git branch, Author/Agent, Workstream      -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->
