# SIH26166 MVP --- Software Requirements Specification

## 1. Scope

-   Project: SIH26166 --- Chandrayaan-2 Image Correspondence
-   Scope: \<15-hour MVP
-   Sensors: OHRC and TMC-2
-   Architecture: separate frontend and backend workstreams
-   Principle: prove one complete, automatic, measurable workflow before
    adding multimodal deep learning, IIRS, or agentic control.

## 2. Repository Structure

``` text
/
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
├── contracts/
├── ground_truth/
├── flow.md
├── progress.md
├── technical-questions.md
└── documentation/
```

## 3. Frontend Requirements

### FE-01 Dashboard

Implement the reference dashboard structure:

1.  Image Pair Preview
2.  Registration Result
3.  Correspondence Distribution
4.  Reprojection Error
5.  Transformation Summary
6.  Ground-Truth Validation
7.  key metrics
8.  export controls

### FE-02 Mock Mode

The frontend MUST work without the backend.

Use:

``` text
frontend/mock/result.json
```

This allows dashboard development in parallel.

### FE-03 Image Pair Preview

Display:

-   source image;
-   reference image;
-   filenames;
-   sensor;
-   dimensions;
-   resolution;
-   correspondence visualization;
-   source/reference selectors;
-   Run Registration.

### FE-04 Correspondence Visualization

Render source/reference point pairs as colored lines.

Support:

-   all matches;
-   filtered matches;
-   RANSAC inliers.

### FE-05 Before/After

Provide:

-   before image;
-   registered image;
-   overlay/blink comparison;
-   slider if practical.

### FE-06 Metrics

Display:

-   feature count;
-   tentative matches;
-   filtered matches;
-   inliers;
-   inlier ratio;
-   reprojection mean;
-   median;
-   RMSE;
-   95th percentile.

### FE-07 Validation

Display independently:

-   ground-truth type;
-   reference source;
-   control-point count;
-   ground-truth mean error;
-   ground-truth median;
-   RMSE;
-   95th percentile;
-   spatial coverage;
-   validation status.

### FE-08 Evidence Labels

The UI must clearly distinguish:

``` text
MATCH QUALITY
GEOMETRIC SELF-CONSISTENCY
GROUND-TRUTH ACCURACY
```

### FE-09 Failure State

Support:

``` text
SUCCESS
SUCCESS_WITHOUT_INDEPENDENT_VALIDATION
LOW_CONFIDENCE
FAILURE
```

### FE-10 Export

Expose links/buttons for backend artifacts.

## 4. Backend Requirements

### BE-01 Input

Accept source and reference images.

Validate:

-   readable file;
-   dimensions;
-   metadata where available;
-   sensor identity where available.

### BE-02 Pair Analysis

Calculate:

-   dimensions;
-   approximate scale/resolution difference;
-   contrast characteristics;
-   basic texture;
-   optional blur indicator;
-   metadata availability.

### BE-03 Preprocessing

Initial operations:

-   grayscale;
-   contrast normalization;
-   optional CLAHE;
-   optional working-resolution resize;
-   optional mild noise handling.

Maintain coordinate mapping between working and original resolution.

Do not claim to remove Sun angle.

### BE-04 SIFT

Output:

-   keypoints;
-   descriptors;
-   feature count.

### BE-05 Matching

Support:

-   BFMatcher or FLANN;
-   nearest-neighbor matching;
-   Lowe ratio;
-   optional mutual consistency.

### BE-06 Geometry

Use:

``` text
candidate correspondences
→ RANSAC
→ inliers
→ homography
```

Optionally compare affine if time permits.

### BE-07 Registration

Warp source into reference coordinates.

Generate:

-   registered image;
-   overlay-ready output;
-   transformation matrix.

### BE-08 Metrics

Calculate:

-   tentative matches;
-   filtered matches;
-   inliers;
-   inlier ratio;
-   reprojection mean;
-   median;
-   RMSE;
-   high percentile;
-   spatial coverage.

### BE-09 Ground-Truth Validation

Input:

``` text
source ground-truth coordinate
reference ground-truth coordinate
predicted reference coordinate
```

Calculate:

-   mean error;
-   median error;
-   RMSE;
-   percentile error;
-   spatial coverage;
-   pass/fail status.

Do not use evaluation control points to fit the transformation.

### BE-10 Synthetic Validation

Support known transformations:

-   translation;
-   rotation;
-   scale;
-   mild perspective.

Compare recovered coordinates against mathematically known coordinates.

Synthetic validation proves implementation correctness, not real lunar
accuracy.

### BE-11 API

Minimum endpoints:

``` text
GET  /health
GET  /pairs
POST /register
GET  /results/{id}
GET  /results/{id}/artifact/{name}
```

If a simpler local interface is necessary during the 15-hour MVP,
preserve the same logical contract.

## 5. Result Contract

The backend result must contain:

``` text
pair
preprocessing
matching
geometry
registration
validation
artifacts
status
```

The frontend must not depend on internal backend module names.

## 6. Coordinate Requirements

Track explicitly:

``` text
original image
→ working image
→ feature coordinates
→ reference coordinates
```

Every resize/downsample operation must preserve the scale mapping.

Every accuracy metric must state its coordinate system.

## 7. Data Requirements

MVP execution target:

-   3 selected real OHRC ↔ TMC-2 pairs;
-   one demonstration;
-   one validation pair;
-   one difficult pair.

Ground-truth dataset target:

-   15--20 candidate OHRC ↔ TMC-2 pairs;
-   approximately 30--50 reference points per usable pair where
    available.

Current reference dataset contains derived geographic correspondences
but lacks manually verified real-image pixel correspondences. Treat its
limitations explicitly.

## 8. Validation Rules

### Synthetic

Known transformation → run pipeline → compare recovery.

### Real

Independent control/reference points → run pipeline without using them
for fitting → calculate ground-truth error.

### Difficult

Run a challenging pair and record failure/low-confidence behavior.

Never equate:

``` text
reprojection error
=
ground-truth error
```

## 9. Frontend/Backend Integration

Integration occurs only through the agreed contract.

Frontend development must not require a functioning backend.

Backend development must not require the completed dashboard.

Use:

``` text
frontend/mock/result.json
```

until backend API is available.

When integrated:

``` text
Frontend
   ↓ HTTP/API
Backend
   ↓
Pipeline
   ↓
Result JSON
   ↓
Frontend
```

## 10. Non-Functional Requirements

### Reproducibility

Record:

-   input IDs;
-   preprocessing configuration;
-   matcher configuration;
-   RANSAC parameters;
-   software version.

### Explainability

Expose:

-   feature count;
-   candidate matches;
-   filtered matches;
-   inliers;
-   transformation;
-   reprojection metrics;
-   ground-truth metrics;
-   runtime.

### Performance

The MVP must run on a normal laptop for selected demonstration pairs.

### Scientific integrity

Never fabricate:

-   ground truth;
-   accuracy;
-   control points;
-   overlap;
-   validation results.

## 11. Out of Scope

-   IIRS;
-   production RIFT2;
-   production LoFTR;
-   production SuperGlue;
-   training/fine-tuning;
-   full sub-pixel refinement;
-   LLM numerical control;
-   autonomous agent;
-   cloud deployment;
-   authentication;
-   large-scale infrastructure.

## 12. Acceptance Criteria

``` text
[ ] Frontend starts independently
[ ] Frontend renders mock result
[ ] Backend starts independently
[ ] Backend processes one real pair
[ ] API returns agreed result schema
[ ] Frontend consumes real backend result
[ ] Correspondences visible
[ ] RANSAC inliers visible
[ ] Registration output visible
[ ] Transformation visible
[ ] Reprojection metrics visible
[ ] Ground-truth metrics separate
[ ] Synthetic validation works
[ ] 3 real pairs tested
[ ] Failure case recorded
[ ] Export works
[ ] No unsupported accuracy claim
```
