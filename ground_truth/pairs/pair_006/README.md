# pair_006 — Southern_56E

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200824T1003365280_d_img_d18` |
| TMC-2 | `ch2_tmc_ncn_Southern_56E_grd` |
| Quality | **B** |
| GT Type | `DERIVED_CORRESPONDENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | NO |

## OHRC Sensor
- Resolution: 0.2581 m/px | Dims: 93692×12000px
- UL (-61.6605°,56.5770°) UR (-61.6574°,56.8074°)
- LL (-62.4900°,56.6665°) LR (-62.4869°,56.9029°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: GRD
- Note: IIT confirmed. ~61-63S,56-57E. Exact product ID: run IIT overlap script.

## Ground Truth Classification: DERIVED_CORRESPONDENCE
IIT confirmed. Parallel track 2h later.

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
raw/source_ohrc_ch2_ohr_ncp_20200824T1003365280_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ncn_Southern_56E_grd.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
