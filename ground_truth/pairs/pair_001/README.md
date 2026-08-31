# pair_001 — South_Polar_41E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200825T1127278043_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_SouthPolar_41E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2495 m/px | Dims: 93693×12000px
- UL (-68.3626°,41.1413°) UR (-68.3598°,41.4205°)
- LL (-69.1975°,41.1925°) LR (-69.1947°,41.4820°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed. 6x OHRC overlap. ~68-69S,40-42E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. USGS/ASP similar region. Best south-polar pair.

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
raw/source_ohrc_ch2_ohr_ncp_20200825T1127278043_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_SouthPolar_41E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
