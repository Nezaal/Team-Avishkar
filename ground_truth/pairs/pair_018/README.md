# pair_018 — Mid_South_25E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20210401T2357376656_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_MidSouth_25E_grd` |
| Quality | **C** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2649 m/px | Dims: 90148×12000px
- UL (-13.0584°,25.1331°) UR (-13.0553°,25.2459°)
- LL (-13.8889°,25.1284°) LR (-13.8858°,25.2416°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: Inferred. ~12-14S,25E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
2021 OHRC parallel track over TMC-MID2.

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
raw/source_ohrc_ch2_ohr_ncp_20210401T2357376656_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_MidSouth_25E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
