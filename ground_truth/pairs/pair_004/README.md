# pair_004 — South_Polar_43E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200229T0938004033_d_img_d32` |
| TMC-2 | `ch2_tmc_ncn_SouthPolar_43E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 0 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2302 m/px | Dims: 93693×12000px
- UL (-73.9204°,42.7994°) UR (-73.9125°,42.4571°)
- LL (-73.0789°,43.0316°) LR (-73.0714°,42.7063°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed. ~73-74S,42-44E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. d32 product same region.

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
raw/source_ohrc_ch2_ohr_ncp_20200229T0938004033_d_img_d32.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_SouthPolar_43E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
