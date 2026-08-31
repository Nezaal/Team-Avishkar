# technical-questions.md — SIH26166 Technical Knowledge Base

> **Rule:** This file is living — questions are added at any time by any branch.
> Every question MUST include `Branch-raised:` and `Last-updated-by:` fields.
> When two branches edit the same question, the merger must combine both answers
> based on evidence and record the resolution in `progress.md`.
> New questions go at the bottom of the OPEN section.

---

## OPEN Questions

---

### Q1: What are the exact TMC-2 product IDs for our 20 pairs?

```
Status:          OPEN
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/sources/, ground_truth/manifests/pairs.csv
```

**Context:**
The IIT team identified 18 OHRC/TMC-2 overlapping patches from 6 unique TMC-2 scenes,
but their CSV contains 1,083 records and does not explicitly list the 6 chosen IDs.
19 of our 20 pairs use provisional TMC-2 product names. Only pair_012 has a confirmed
exact ID (from USGS/ASP documentation).

**Answer:**
UNKNOWN for 19 pairs. Known for 1 (pair_012: ch2_tmc_ndn_20231101T0125121377_d_oth_d18).

**Evidence:**
- USGS/ASP documentation confirms pair_012 TMC-2 ID.
- IIT coordinates_tmc2_iit.csv has 1,083 records but no explicit overlap list.

**Decision:**
Use provisional names for now. Run IIT ohrc_tmc_overlap.py (GT-07 task) to recover
exact IDs. Do not download TMC-2 images without confirmed product IDs.

**Confidence:** LOW (for 19 pairs)

---

### Q2: How do we compute TMC-2 pixel coordinates for control points?

```
Status:          OPEN
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/sources/build_dataset.py, ground_truth/control_points/
```

**Context:**
All 612 control points have `reference_x = UNKNOWN` and `reference_y = UNKNOWN`
because the IIT coordinates_tmc2.csv does not include TMC-2 image dimensions
(shape_x, shape_y). Without dimensions, bilinear interpolation into TMC-2 pixel
space is impossible.

**Answer:**
Cannot be computed until at least one TMC-2 .img file is downloaded and its PDS
header is parsed for LINES and LINE_SAMPLES values.

**Evidence:**
manifests/pairs.csv columns reference_width = UNKNOWN, reference_height = UNKNOWN for all 20 pairs.

**Decision:**
Download TMC-2 image (GT-02 task), read header dims (GT-03 task),
then re-run build_dataset.py (GT-09 task).

**Confidence:** HIGH (process is clear, blocked on image download only)

---

### Q3: How will we validate sub-pixel accuracy claims?

```
Status:          OPEN
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/control_points/, backend/validation/
```

**Context:**
All 612 current control points are `geospatially_derived`. They are NOT manually
verified pixel correspondences. They cannot support sub-pixel accuracy claims.
The 5 synthetic GT samples provide exact sub-pixel ground truth but only for
synthetic (transformed) images — not real lunar imagery.

**Answer:**
Currently cannot validate sub-pixel accuracy on real images.

Two paths to fix:
1. Manual annotation: ~30 pixel-exact correspondences for pairs 001, 012, 003
   (GT-05 task — requires image download first).
2. Synthetic validation: already available via synthetic_gt.csv
   (proves implementation correctness, not real lunar accuracy).

**Evidence:**
validation/ground_truth_report.md §6: "How many exact pixel-level GT points? Zero on real images."

**Decision:**
Report synthetic validation results separately from real-image results.
Never present reprojection error as ground-truth accuracy.
Label all 612 derived CPs as geospatially_derived in all outputs.

**Confidence:** HIGH (limitation is clearly understood)

---

### Q4: Will SIFT produce sufficient keypoints on extreme south-polar lunar imagery?

```
Status:          OPEN
Branch-raised:   main (raised during planning)
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: backend/pipeline/sift.py (not yet built)
```

**Context:**
South polar lunar imagery (pair_003: 73-74°S) has very low solar elevation,
high shadow fraction, and low surface texture. SIFT relies on gradient features.
It may fail in heavily shadowed or near-uniform regions.

**Answer:**
UNKNOWN — no experiments yet. SIFT is the MVP baseline because it is mature,
CPU-friendly, and explainable. Whether it works on extreme polar pairs is an
open empirical question.

**Evidence:**
None yet — backend pipeline not built.

**Decision:**
Attempt SIFT first. If keypoint count is < 500 on a polar pair, investigate
CLAHE preprocessing or consider RIFT2 as a future improvement (post-MVP).

**Confidence:** LOW (no experimental evidence)

---

### Q5: What working resolution should we use for OHRC images during SIFT?

```
Status:          OPEN
Branch-raised:   main (raised during planning)
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: backend/pipeline/preprocessor.py (not yet built)
```

**Context:**
OHRC images are very large (e.g., 93,693 × 12,000 pixels at 0.25m/px).
Running SIFT at full resolution would be impractical on a laptop.
The MVP must run on a normal laptop for demonstration pairs.

**Answer:**
UNKNOWN — needs empirical testing. A working scale of 0.1 to 0.25 (10-25% of
original) is a reasonable starting range. Scale factor must be preserved and
applied to convert keypoint coordinates back to original resolution for metric
reporting.

**Evidence:**
None yet — backend not built.

**Decision:**
Start with 0.25 working scale (25% of original). Record scale factor in
preprocessing output. If SIFT is too slow, reduce further. If keypoint count
is too low, increase.

**Confidence:** LOW (needs experimentation)

---

## RESOLVED Decisions

---

### D1: Dataset Scope

```
Status:          ANSWERED
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/
```

**Decision:**
Build a pure data engineering dataset (20 pairs, metadata, scripts) without
running any CV pipeline code.

**Rationale:**
Follows strict instruction: "Your ONLY task is to research, scrape, download,
extract, normalize, and organize ground-truth/reference data."

**Confidence:** HIGH

---

### D2: Control Point Provenance Labeling

```
Status:          ANSWERED
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/control_points/, ground_truth/sources/build_dataset.py
```

**Decision:**
Explicitly label all 612 derived control points with:
- `verification_method = geospatially_derived`
- `accuracy = sub-degree_geographic_only`

**Rationale:**
Prevents false claims of sub-pixel accuracy. The points are mathematically
interpolated from corner metadata, not manually measured.

**Confidence:** HIGH

---

### D3: Independent Reference Selection

```
Status:          ANSWERED
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: ground_truth/pairs/pair_012/
```

**Decision:**
Identify pair_012 as the sole `GEOREFERENCED_REFERENCE` pair, backed by
LOLA DEM data via USGS/ASP documentation.

**Rationale:**
Provides at least one pair with a documented, independent (non-Chandrayaan-2)
reference source for robust validation.

**Confidence:** HIGH

---

### D4: Parallel Frontend/Backend Architecture

```
Status:          ANSWERED
Branch-raised:   main
Last-updated-by: Antigravity (AI agent)
Last updated:    2026-08-31
Related modules: frontend/, backend/, contracts/
```

**Decision:**
Build frontend and backend as independent workstreams that communicate only
through a shared result JSON contract. Frontend uses mock data until backend
API is ready.

**Rationale:**
Allows parallel development without blocking either team. Matches the
15-hour sprint plan in doc/SIH26166_MVP_PLAN.md.

**Confidence:** HIGH

---

<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- NEW OPEN QUESTIONS GO ABOVE THE RESOLVED SECTION                       -->
<!-- Format: ### Q<N>: <question>                                            -->
<!-- MANDATORY: Status, Branch-raised, Last-updated-by, Last updated        -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->
