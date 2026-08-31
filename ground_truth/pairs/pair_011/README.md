# pair_011 — South_Polar_20E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200827T0030107497_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_SouthPolar_20E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2370 m/px | Dims: 101075×12000px
- UL (-67.8979°,20.8052°) UR (-67.8923°,21.0692°)
- LL (-68.7375°,20.8489°) LR (-68.7318°,21.1226°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed + USGS/ASP region. ~64-69S,20-21E. LOLA independent ref available.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. USGS/ASP documented region ~20E. LOLA available.

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
raw/source_ohrc_ch2_ohr_ncp_20200827T0030107497_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_SouthPolar_20E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
