# pair_015 — Equatorial_South_70E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20190906T1246532096_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_Equatorial_70E_grd` |
| Quality | **C** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 0 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2700 m/px | Dims: 63230×12000px
- UL (-14.3238°,71.3343°) UR (-16.7298°,69.1749°)
- LL (-14.7350°,71.4457°) LR (-17.1563°,69.2998°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: Inferred. ~14-17S,69-71E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
2019 OHRC. Earliest scene. Overlap inferred from coordinates.

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
raw/source_ohrc_ch2_ohr_ncp_20190906T1246532096_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_Equatorial_70E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
