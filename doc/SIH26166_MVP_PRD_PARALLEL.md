# SIH26166 MVP --- Product Requirements Document

## 1. Product

**Chandrayaan-2 Autonomous Image Correspondence MVP**

> An explainable lunar image-registration system that automatically
> discovers corresponding terrain points between Chandrayaan-2 images,
> geometrically verifies them, registers the images, and quantitatively
> validates the result.

The MVP is a working technical prototype, not the final
multimodal/IIRS/sub-pixel system.

## 2. Objective

Demonstrate:

1.  real Chandrayaan-2 imagery;
2.  automatic correspondence;
3.  geometric verification;
4.  registration;
5.  transparent metrics;
6.  independent validation where available;
7.  reproducible outputs;
8.  a credible path toward the full system.

The MVP focuses on OHRC ↔ TMC-2 optical registration.

## 3. MVP Product Flow

``` text
USER
 ↓
FRONTEND
 ↓
select OHRC + TMC-2
 ↓
BACKEND API
 ↓
pair analysis
 ↓
preprocessing
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
RESULT JSON + ARTIFACTS
 ↓
FRONTEND
 ↓
dashboard
```

## 4. Parallel Product Architecture

``` text
project/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── mock/
│   └── assets/
│
├── backend/
│   ├── api/
│   ├── pipeline/
│   ├── validation/
│   ├── models/
│   └── tests/
│
├── ground_truth/
├── contracts/
└── docs/
```

### Frontend owns

-   dashboard;
-   visualization;
-   interaction;
-   presentation;
-   mock-data mode;
-   API response rendering.

### Backend owns

-   CV pipeline;
-   validation;
-   computation;
-   artifact generation;
-   API;
-   result schema.

## 5. Dashboard

The dashboard must reproduce the core technical evidence shown in the
reference design.

### A. Image Pair Preview

Show:

-   OHRC image;
-   TMC-2 image;
-   filename;
-   sensor;
-   dimensions;
-   nominal resolution;
-   correspondence lines;
-   match counts;
-   source/reference selectors;
-   Run Registration.

### B. Registration Result

Show:

-   before registration;
-   after registration;
-   overlay/blink slider;
-   registration status.

Do not imply SIH-grade accuracy merely because registration completed.

### C. Correspondence Distribution

Show:

-   source-image point scatter;
-   total correspondences;
-   filtered matches;
-   RANSAC inliers;
-   inlier ratio;
-   spatial/grid coverage.

### D. Reprojection Error

Show:

-   histogram;
-   mean;
-   median;
-   RMSE;
-   percentile;
-   threshold indicator.

Label this:

**Transformation self-consistency**

Never call it ground-truth accuracy.

### E. Transformation Summary

Show:

-   model;
-   transformation matrix;
-   inliers;
-   inlier ratio;
-   reprojection statistics.

### F. Ground-Truth Validation

Separate panel:

``` text
Ground-Truth Validation
Points
Mean Error
Median Error
RMSE
95th Percentile
Spatial Coverage
Validation Status
Reference Type
```

## 6. Backend MVP

The backend must implement:

``` text
Input validation
→ pair analysis
→ basic pair-aware preprocessing
→ SIFT
→ BFMatcher/FLANN
→ Lowe ratio
→ optional mutual consistency
→ RANSAC
→ homography
→ warp
→ metrics
→ ground-truth validation
→ artifact export
```

SIFT is the baseline because it is mature, CPU-friendly, explainable,
and fast to establish a measurable baseline.

RANSAC is required because descriptor matching contains outliers and
transformation estimation needs robust geometric verification.

## 7. Ground Truth

The target ground-truth collection is 15--20 OHRC ↔ TMC-2 pairs.

Current collected reference dataset reports:

-   20 pairs;
-   17 pairs with derived control points;
-   612 derived control points;
-   only one pair with an external LOLA reference;
-   zero manually verified real-image pixel correspondences.

Therefore:

**Do not describe the 612 derived points as manually verified ground
truth.**

Real-image sub-pixel accuracy cannot currently be claimed from this
dataset.

Synthetic known-transformation validation is valid for implementation
correctness.

## 8. Metrics

### Match quality

-   feature count;
-   tentative matches;
-   filtered matches;
-   inliers;
-   inlier ratio.

### Geometric consistency

-   mean reprojection error;
-   median;
-   RMSE;
-   high percentile;
-   error distribution.

### True validation

-   ground-truth mean error;
-   median;
-   RMSE;
-   95th percentile;
-   spatial coverage;
-   failure rate.

The dashboard must keep these three categories separate.

## 9. API Contract

Frontend must be able to operate using a saved mock response.

Minimum response:

``` json
{
  "pair": {
    "source": {},
    "reference": {}
  },
  "preprocessing": {
    "operations": [],
    "parameters": {}
  },
  "matching": {
    "features_source": 0,
    "features_reference": 0,
    "tentative": 0,
    "filtered": 0,
    "inliers": 0,
    "inlier_ratio": 0
  },
  "geometry": {
    "model": "homography",
    "matrix": [],
    "reprojection": {}
  },
  "registration": {
    "status": "",
    "registered_image": ""
  },
  "validation": {
    "ground_truth_type": "",
    "points": 0,
    "mean_error_px": null,
    "median_error_px": null,
    "rmse_px": null,
    "p95_error_px": null,
    "spatial_coverage": null,
    "status": ""
  },
  "artifacts": {
    "matches": "",
    "metrics": "",
    "transformation": "",
    "registered_image": ""
  },
  "status": {
    "level": "",
    "message": ""
  }
}
```

## 10. Explicitly Out of Scope

-   IIRS;
-   production RIFT2;
-   production LoFTR;
-   production SuperGlue;
-   neural training;
-   fine-tuning;
-   full sub-pixel refinement;
-   LLM-based numerical registration;
-   full autonomous agent;
-   accounts/authentication;
-   cloud deployment;
-   mobile app;
-   3D rendering;
-   large-scale infrastructure.

## 11. Definition of Done

The MVP is ready when:

-   one real OHRC ↔ TMC-2 pair runs automatically;
-   frontend shows correspondence lines;
-   registered output is generated;
-   RANSAC inliers are visible;
-   transformation is visible;
-   reprojection metrics are visible;
-   ground-truth validation is separate;
-   at least 3 real pairs are tested;
-   synthetic validation exists;
-   one independent validation experiment exists where available;
-   outputs can be exported;
-   failure behavior is visible;
-   no unsupported accuracy claim is made;
-   frontend and backend can run independently before final integration.
