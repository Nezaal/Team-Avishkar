# pair_017 — Mid_South_25E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20210401T2200364910_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_MidSouth_25E_grd` |
| Quality | **C** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2660 m/px | Dims: 76619×12000px
- UL (-12.9411°,25.1623°) UR (-12.9622°,25.3033°)
- LL (-13.7703°,25.1540°) LR (-13.7915°,25.2956°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: Inferred. ~12-14S,25E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
2021 OHRC. ~12-14S, 25E. Different region.

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
raw/source_ohrc_ch2_ohr_ncp_20210401T2200364910_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_MidSouth_25E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
