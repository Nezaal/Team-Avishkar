# pair_016 — Mid_South_41E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20210331T2033243734_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_MidSouth_41E_grd` |
| Quality | **C** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2679 m/px | Dims: 90148×12000px
- UL (-19.6949°,41.4065°) UR (-19.6959°,41.5232°)
- LL (-20.5242°,41.4141°) LR (-20.5251°,41.5315°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: Inferred. ~19-21S,41E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
2021 OHRC. ~19-21S, 41E. Different epoch.

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
raw/source_ohrc_ch2_ohr_ncp_20210331T2033243734_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_MidSouth_41E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
