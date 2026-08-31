# AGENT.md --- SIH26166 Development Memory & Documentation Controller

## 1. Role

You are the development agent for SIH26166.

The project is divided into two independently executable workstreams:

``` text
frontend/  → dashboard and presentation
backend/   → image-registration pipeline and validation
```

The two workstreams must be developed in parallel through a stable
data/API contract.

Maintain these living files:

-   `flow.md`
-   `progress.md`
-   `technical-questions.md`

Do not assume architecture is permanently fixed.

## 2. Mandatory Startup

Before development:

1.  Read `AGENT.md`.
2.  Read `flow.md`.
3.  Read `progress.md`.
4.  Read `technical-questions.md`.
5.  Inspect Git branch and working tree.
6.  Inspect the relevant `frontend/` or `backend/` code.
7.  Determine whether the task changes architecture, interfaces,
    algorithms, validation, or configuration.

Do not modify the other workstream unless the task explicitly requires
integration.

## 3. Workstream Boundaries

### Frontend

Owns:

-   dashboard layout;
-   image pair preview;
-   source/reference selectors;
-   correspondence visualization;
-   before/after registration;
-   image overlay/blink;
-   correspondence distribution;
-   reprojection histogram;
-   transformation summary;
-   ground-truth validation panel;
-   status/confidence presentation;
-   export/download controls;
-   mock-data mode.

Frontend does NOT own:

-   SIFT;
-   matching;
-   RANSAC;
-   homography estimation;
-   image registration;
-   ground-truth computation;
-   CV preprocessing.

### Backend

Owns:

-   image loading;
-   metadata inspection;
-   pair analysis;
-   preprocessing;
-   SIFT;
-   descriptor matching;
-   filtering;
-   RANSAC;
-   transformation estimation;
-   registration/warping;
-   correspondence metrics;
-   validation;
-   synthetic validation;
-   result serialization/API.

Backend does NOT own:

-   dashboard layout;
-   visual styling;
-   frontend state;
-   presentation logic.

## 4. Interface Contract

Frontend and backend communicate only through the agreed result
schema/API.

The frontend must be runnable with mock JSON before backend integration.

Minimum result contract:

``` json
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

Any contract change must be recorded in:

-   `flow.md`
-   `progress.md`
-   `technical-questions.md` when technically significant.

## 5. Technical Integrity

Never:

-   fabricate accuracy;
-   fabricate ground truth;
-   call reprojection error ground-truth accuracy;
-   claim sub-pixel accuracy without appropriate validation;
-   use visual quality as proof of accuracy;
-   hide failed experiments;
-   silently change coordinate direction or coordinate system.

If evidence is missing, mark it `OPEN` or `UNKNOWN`.

## 6. Current MVP Boundary

The MVP is a real OHRC ↔ TMC-2 optical registration vertical slice:

``` text
OHRC + TMC-2
    ↓
pair analysis
    ↓
basic pair-aware preprocessing
    ↓
SIFT
    ↓
matching
    ↓
filtering
    ↓
RANSAC
    ↓
homography
    ↓
registration
    ↓
validation
    ↓
API/result contract
    ↓
dashboard
```

RIFT2, LoFTR, SuperGlue, IIRS, full sub-pixel refinement, LLM control,
and a full autonomous agent remain outside the MVP.

## 7. Documentation Rules

`flow.md` = current architecture only.

`progress.md` = development history, including Git branch.

`technical-questions.md` = evolving technical knowledge and unresolved
questions.

For every meaningful change:

-   inspect Git branch;
-   update `progress.md`;
-   update `flow.md` if architecture/interface changes;
-   update `technical-questions.md` if technical understanding changes.

Do not put future architecture into `flow.md` until implemented.

## 8. Parallel Development Rule

Frontend and backend may progress independently.

Frontend can use:

``` text
frontend/mock/
```

Backend can expose:

``` text
backend/api/
```

Integration happens only after the result contract is stable.

Do not block frontend development waiting for the CV pipeline.

Do not block backend development waiting for the dashboard.

## 9. Completion Checklist

``` text
[ ] Read current documentation
[ ] Inspect Git branch
[ ] Inspect relevant workstream
[ ] Respect frontend/backend boundary
[ ] Use stable result contract
[ ] Test the changed workstream
[ ] Update flow.md if architecture changed
[ ] Update progress.md
[ ] Update technical-questions.md when needed
[ ] Record unresolved issues
```
