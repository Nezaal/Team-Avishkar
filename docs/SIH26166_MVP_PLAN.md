# SIH26166 MVP --- Parallel Frontend / Backend Implementation Plan

## 1. Goal

Build the MVP in parallel using two independent directories:

``` text
frontend/
backend/
```

The frontend builds the complete dashboard against mock data.

The backend builds the real OHRC ↔ TMC-2 registration pipeline.

They integrate through a fixed result contract.

The existing MVP requirements remain the source of truth: SIFT →
matching → RANSAC → homography → registration → validation → dashboard.
The MVP deliberately excludes RIFT2, LoFTR, SuperGlue, IIRS, full
sub-pixel refinement, LLM control, and a full autonomous agent.

## 2. Final Architecture

``` text
                    ┌────────────────────┐
                    │      FRONTEND      │
                    │     Dashboard      │
                    │                    │
                    │ Streamlit           │
                    └─────────┬──────────┘
                              │
                         HTTP / JSON
                              │
                    ┌─────────▼──────────┐
                    │       BACKEND      │
                    │       API          │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │    Pipeline        │
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
                    └────────────────────┘
```

## 3. Directory Ownership

``` text
frontend/
    Frontend developer owns everything here.

backend/
    Backend/CV developer owns everything here.

contracts/
    Shared interface only.

ground_truth/
    Dataset/reference data only.
```

Do not cross-edit another team's directory unless integration requires
it.

## 4. Shared Contract First

Before substantial implementation, create:

``` text
contracts/result.schema.json
contracts/example_result.json
```

Minimum sections:

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

This is the most important parallel-development dependency.

Frontend uses `example_result.json`.

Backend must eventually produce the same schema.

## 5. FRONTEND PLAN

### F1 --- Skeleton

Create:

``` text
frontend/
├── app/
├── components/
├── mock/
├── assets/
└── README.md
```

Build the page with mock data.

Do not wait for backend.

### F2 --- Image Pair Preview

Implement:

-   source selector;
-   reference selector;
-   image cards;
-   metadata;
-   Run Registration button;
-   correspondence display.

Use local mock images initially.

### F3 --- Registration Result

Implement:

-   before image;
-   after image;
-   overlay;
-   blink/slider;
-   status.

### F4 --- Correspondence Visualization

Implement:

-   source/reference point plotting;
-   correspondence lines;
-   inlier/outlier distinction;
-   point count.

### F5 --- Metrics

Implement:

-   total features;
-   tentative matches;
-   filtered matches;
-   inliers;
-   inlier ratio;
-   reprojection statistics.

### F6 --- Plots

Implement:

-   correspondence distribution;
-   spatial/grid coverage;
-   reprojection histogram.

### F7 --- Transformation

Implement:

-   model name;
-   transformation matrix;
-   inliers;
-   reprojection statistics.

### F8 --- Ground Truth

Implement separate validation panel:

``` text
Ground Truth
Reference Type
Points
Mean Error
Median Error
RMSE
P95
Spatial Coverage
Status
```

Never merge this with reprojection error.

### F9 --- Export

Add:

-   registered image;
-   matches CSV;
-   metrics JSON;
-   transformation JSON;
-   validation report.

### F10 --- API Integration

Replace:

``` text
mock/result.json
```

with backend API response.

Do not redesign the UI during integration.

## 6. BACKEND PLAN

### B1 --- Skeleton

Create:

``` text
backend/
├── api/
├── pipeline/
├── validation/
├── models/
├── tests/
└── README.md
```

### B2 --- Image Loader

Support:

-   TIFF;
-   common raster formats needed by the MVP.

Return:

-   image array;
-   dimensions;
-   metadata;
-   resolution when available.

### B3 --- Pair Analyzer

Calculate:

-   dimensions;
-   resolution difference;
-   contrast;
-   texture;
-   blur indicator;
-   available metadata.

Output configuration information for preprocessing.

### B4 --- Preprocessing

Implement only practical MVP operations:

``` text
grayscale
contrast normalization
optional CLAHE
working-resolution resize
optional mild noise handling
```

Preserve coordinate mapping.

Do not attempt a complex Sun-angle removal algorithm in the 15-hour MVP.

### B5 --- SIFT

Implement:

``` text
image
→ SIFT
→ keypoints
→ descriptors
```

Record feature counts.

### B6 --- Matching

Implement:

``` text
descriptors
→ BFMatcher/FLANN
→ nearest neighbors
→ Lowe ratio
→ optional mutual consistency
```

Return source/reference coordinates.

### B7 --- RANSAC

Implement:

``` text
candidate correspondences
→ RANSAC
→ homography
→ inlier mask
```

Record:

-   matrix;
-   inliers;
-   rejected points;
-   reprojection errors.

### B8 --- Registration

Warp source into reference coordinates.

Generate:

-   registered image;
-   overlay-compatible image;
-   transformation matrix.

### B9 --- Validation

Implement two paths.

#### Synthetic

Known transform:

``` text
image
→ known transform
→ pipeline
→ compare recovered coordinates
```

#### Real

``` text
ground-truth control points
→ predicted coordinates
→ error
→ mean/median/RMSE/P95
```

Never use evaluation points to fit the homography.

### B10 --- Serialization

Produce:

``` text
result.json
matches.csv
transformation.json
metrics.json
registered.png
before_after.png
```

### B11 --- API

Minimum:

``` text
GET  /health
GET  /pairs
POST /register
GET  /results/{id}
GET  /results/{id}/artifact/{name}
```

Keep the API thin. Pipeline logic stays inside `pipeline/`.

## 7. Integration Order

Do NOT wait until everything is complete.

Integrate in this order:

``` text
1. Contract
   ↓
2. Frontend mock
   ↓
3. Backend health API
   ↓
4. Backend result JSON
   ↓
5. Frontend reads real JSON
   ↓
6. Real registered image
   ↓
7. Real correspondence data
   ↓
8. Real metrics
   ↓
9. Real validation
```

## 8. Suggested 15-Hour Parallel Schedule

### Hour 0--1

BOTH:

-   inspect repository;
-   read documentation;
-   create directories;
-   agree contract.

### Hour 1--4

FRONTEND:

-   dashboard skeleton;
-   image pair cards;
-   mock data;
-   registration result panel.

BACKEND:

-   image loader;
-   pair analyzer;
-   preprocessing;
-   SIFT.

### Hour 4--7

FRONTEND:

-   correspondence visualization;
-   before/after;
-   metrics cards;
-   transformation panel.

BACKEND:

-   matching;
-   Lowe ratio;
-   RANSAC;
-   homography;
-   registration.

### Hour 7--9

FRONTEND:

-   distribution plot;
-   reprojection histogram;
-   validation panel.

BACKEND:

-   reprojection metrics;
-   spatial coverage;
-   serialization;
-   synthetic validation.

### Hour 9--11

FRONTEND:

-   API integration;
-   real result rendering.

BACKEND:

-   ground-truth validation;
-   API;
-   artifact generation.

### Hour 11--13

BOTH:

-   integrate;
-   test real pair;
-   fix schema mismatches;
-   test 3 selected pairs.

### Hour 13--15

BOTH:

-   stabilize demo;
-   failure case;
-   export;
-   screenshots;
-   judge evidence.

## 9. Mock Result Strategy

Frontend should immediately receive an example like:

``` json
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
  "matching": {
    "features_source": 18642,
    "features_reference": 12000,
    "tentative": 8000,
    "filtered": 5000,
    "inliers": 12387,
    "inlier_ratio": 0.664
  },
  "geometry": {
    "model": "Homography",
    "matrix": [
      [0.9987, -0.0482, 15.2371],
      [0.0469, 0.9989, -11.4827],
      [0.000001, 0.000002, 1.0]
    ],
    "reprojection": {
      "mean_px": 0.38,
      "median_px": 0.34,
      "rmse_px": 0.47,
      "p95_px": 0.91
    }
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
  "status": {
    "level": "SUCCESS_WITHOUT_INDEPENDENT_VALIDATION"
  }
}
```

These values are UI mock data only. They must never be presented as
measured results.

## 10. Critical Scientific Rule

The dashboard must visually distinguish:

``` text
MATCH QUALITY
      ↓
candidate/filter/inliers

GEOMETRIC SELF-CONSISTENCY
      ↓
reprojection error

TRUE VALIDATION
      ↓
independent ground-truth error
```

The statement:

``` text
0.38 px reprojection error
```

must never become:

``` text
0.38 px accuracy
```

without independent ground truth.

## 11. Team Interface

Frontend asks only for:

``` text
result JSON
artifact URLs/paths
```

Backend provides only:

``` text
API + result contract + artifacts
```

Frontend must not import backend CV modules.

Backend must not import frontend components.

## 12. Final Integration Test

Run:

``` text
select pair
→ frontend request
→ backend registration
→ result JSON
→ dashboard update
→ registered image
→ metrics
→ validation
→ export
```

Success means the entire vertical slice works.

## 13. Final Deliverables

``` text
frontend/
    working dashboard
    mock mode
    API mode
    visualizations
    export controls

backend/
    working CV pipeline
    API
    validation
    artifact generation
    tests

contracts/
    result schema
    example response

ground_truth/
    reference dataset

docs/
    technical evidence
```

## 14. Priority if Time Runs Out

### MUST HAVE

1.  Frontend dashboard
2.  Mock mode
3.  Backend SIFT
4.  Matching
5.  RANSAC
6.  Registration
7.  Result JSON
8.  Before/after
9.  correspondence visualization
10. reprojection metrics
11. synthetic validation
12. 1 real pair end-to-end

### SHOULD HAVE

-   3 real pairs;
-   ground-truth validation;
-   spatial coverage;
-   API artifact endpoints;
-   export.

### CUT FIRST

-   affine comparison;
-   sophisticated preprocessing;
-   strategy selection;
-   RIFT2;
-   LoFTR;
-   SuperGlue;
-   agentic controller;
-   sub-pixel refinement;
-   cloud deployment.

## 15. Architectural Decision

The old single-process concept:

``` text
Streamlit
→ Pipeline Runner
→ CV Pipeline
```

is replaced for parallel development by:

``` text
Streamlit Frontend
→ API
→ Backend CV Pipeline
```

This is an MVP engineering split, not a requirement to build production
microservices.

The objective is parallel development without sacrificing the \<15-hour
vertical slice.
