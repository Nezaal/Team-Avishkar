# pair_020 — South_Polar_341E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20210405T0640233469_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_SouthPolar_341E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2291 m/px | Dims: 93693×12000px
- UL (-68.2758°,341.2689°) UR (-68.2813°,341.5391°)
- LL (-69.1196°,341.2362°) LR (-69.1252°,341.5165°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT implied. ~68-69S,341E (=-19W). Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
2021 OHRC parallel track, 341E south polar.

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
raw/source_ohrc_ch2_ohr_ncp_20210405T0640233469_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_SouthPolar_341E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
