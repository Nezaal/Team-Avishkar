# pair_007 — Southern_39E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200825T1322594314_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_Southern_39E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2514 m/px | Dims: 90148×12000px
- UL (-63.3228°,39.4591°) UR (-63.3224°,39.7057°)
- LL (-64.1565°,39.4824°) LR (-64.1563°,39.7362°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed. ~63-65S,39-40E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. ~63-64S, 39E.

## ⚠ Critical Limitations
- Control points are GEOSPATIALLY DERIVED from corner coordinate interpolation
- TMC-2 pixel coordinates are UNKNOWN (image dimensions not in source CSV)
- NOT manually verified correspondences
- CANNOT support sub-pixel accuracy claims
- Images NOT downloaded (PRADAN login required)

## Directory Structure for Registration Pipeline
- `raw/`: **Only** for the original, unmodified `.img` files downloaded from ISRO PRADAN. 
- `processed/`: **Only** for CV pipeline outputs (e.g. SIFT keypoints, matching visualizations, homography matrices). No modified images are stored here.

```
raw/source_ohrc_ch2_ohr_ncp_20200825T1322594314_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_Southern_39E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
