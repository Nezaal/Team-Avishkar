# pair_012 — South_Polar_20E_USGS

| Field | Value |
|-------|-------|
| OHRC | `ch2_ohr_ncp_20200827T0226453039_d_img_d18` |
| TMC-2 | `ch2_tmc_ndn_20231101T0125121377_d_oth_d18` |
| Quality | **B** |
| GT Type | `GEOREFERENCED_REFERENCE` |
| Control Points | 36 (geospatially derived) |
| Pixel-level GT | NO |
| Sub-pixel GT | NO |
| Independent | YES (LOLA) |

## OHRC Sensor
- Resolution: 0.2358 m/px | Dims: 101075×12000px
- UL (-67.9110°,20.7707°) UR (-67.9126°,21.0429°)
- LL (-68.7493°,20.8413°) LR (-68.7506°,21.1233°)
- Download: https://pradan.issdc.gov.in/ch2/ (login required)

## TMC-2 Reference
- Resolution: 5.0 m/px | Product: OTH/DTM
- Note: USGS/ASP explicitly documented OTH product. LOLA DEM comparison documented.

## Ground Truth Classification: GEOREFERENCED_REFERENCE
USGS/ASP explicitly documented. TMC-2 OTH product named in ASP docs. LOLA comparison documented.

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
raw/source_ohrc_ch2_ohr_ncp_20200827T0226453039_d_img_d18.img  ← PRADAN download required
raw/reference_tmc2_ch2_tmc_ndn_20231101T0125121377_d_oth_d18.img  ← PRADAN download required
processed/  ← Leave empty. CV pipeline saves metadata/visualizations here.
```
