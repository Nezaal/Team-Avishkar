# pair_010 — Southern_31E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200826T0853204550_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_Southern_31E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2504 m/px | Dims: 93692×12000px
- UL (-65.8165°,31.5758°) UR (-65.8157°,31.8568°)
- LL (-66.6459°,31.6851°) LR (-66.6444°,31.9752°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed. ~65-67S,31-32E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. ~66S, 31E, parallel track.

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
raw/source_ohrc_ch2_ohr_ncp_20200826T0853204550_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_Southern_31E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
