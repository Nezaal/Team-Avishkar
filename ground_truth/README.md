# SIH26166 Ground Truth Dataset

> **Built:** 2026-08-31 | **Version:** 1.0.0
> **Project:** SIH26166 — Chandrayaan-2 Image Correspondence MVP

---

## Dataset Purpose

This dataset provides ground-truth and reference data for the **SIH26166 OHRC ↔ TMC-2 image registration MVP**.

It is the scientific foundation for validating the CV pipeline. Every pair, control point, and classification was assembled under strict honesty rules:
- No fabricated coordinates
- No SIFT matches presented as ground truth
- No sub-pixel claims without independent evidence
- No duplicate scenes to inflate pair count

---

## Target

**15–20 OHRC ↔ TMC-2 pairs** covering different lunar regions, terrain types, illumination conditions, and scales.

**Achieved: 20 pairs** — 16 quality-B, 4 quality-C.

---

## Dataset Composition

| Category | Count |
|----------|-------|
| Total pairs | **20** |
| OHRC ↔ TMC-2 pairs | **20** (100%) |
| Quality A (strong) | 0 |
| Quality B (useful) | 16 |
| Quality C (weak) | 4 |
| Pairs with control points | 17 |
| Total control points | **612** |
| Independent references | **1** (USGS/ASP + LOLA) |
| Synthetic GT samples | 5 |

---

## Ground-Truth Definitions

| Label | Meaning |
|-------|---------|
| `EXACT_SYNTHETIC_GT` | Known transformation applied to real image; exact pixel-level GT |
| `MANUAL_CONTROL_POINTS` | Human-annotated pixel correspondences; **NONE in this dataset** |
| `INDEPENDENT_CONTROL_POINTS` | Independently measured points; **NONE in this dataset** |
| `GEOREFERENCED_REFERENCE` | Documented georeferenced product with external reference (LOLA); **1 pair** |
| `DERIVED_CORRESPONDENCE` | Pixel coords derived from corner-coordinate georeferencing; **19 pairs** |
| `DEM_REFERENCE` | DEM-based validation; not primary GT type here |
| `WEAK_REFERENCE` | Contextual reference only; not used |

### ⚠ Critical Distinction

> **Reprojection error ≠ ground-truth error.**
> All 612 control points are `geospatially_derived` from corner coordinate bilinear interpolation.
> They are NOT manually verified pixel correspondences.
> They CANNOT support sub-pixel accuracy claims.
> Only pair_012 has an external independent reference (LOLA DEM via USGS/ASP).

---

## Data Sources

### Primary: IIT InterIIT Tech Meet 11.0 Repository
- **URL:** https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0
- **License:** Apache-2.0
- **Contents:** `coordinates_ohrc.csv` (25 OHRC scenes), `coordinates_tmc2.csv` (1,083 TMC-2 records)
- **Team reported:** 18 confirmed OHRC/TMC overlapping patches from 6 unique TMC scenes
- **Methodology:** Haversine-distance corner containment test; bilinear interpolation of OHRC coords into TMC space

### Secondary: USGS / Ames Stereo Pipeline Documentation
- **URL:** https://stereopipeline.readthedocs.io/en/latest/examples/chandrayaan2.html
- **Contents:** Explicit OHRC + TMC-2 product IDs for south polar ~20°E region, LOLA comparison
- **Used for:** pair_012 (GEOREFERENCED_REFERENCE)

### Independent Reference: NASA LOLA
- **URL:** https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
- **Resolution:** 120m/px (LDEM_60S), 60m/px (LDEM_75S)
- **Role:** Independent lunar reference for pair_012 region validation ONLY
- **Not used as:** OHRC/TMC pixel-level ground truth

### Official Data Archive: ISRO PRADAN
- **URL:** https://pradan.issdc.gov.in/ch2/
- **Status:** Login required — images NOT downloaded
- **Available without login:** Corner coordinate metadata (from IIT CSV)

---

## Directory Structure for Registration Pipeline

Inside each `pairs/pair_NNN/` directory:
- `raw/`: **Only** for the original, unmodified `.img` files downloaded from ISRO PRADAN. 
- `processed/`: **Only** for CV pipeline outputs (e.g. SIFT keypoints, matching visualizations, homography matrices). No modified images are stored here. This is an image registration pipeline, not an image generation pipeline.

---

## Pair Inventory

| pair_id | OHRC Scene | Region | Quality | GT Type | CPs | Independent |
|---------|-----------|--------|---------|---------|-----|-------------|
| pair_001 | 20200825T1127278043 | South_Polar_41E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_002 | 20200825T1521048453 | South_Polar_41E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_003 | 20200229T0739312111 | South_Polar_43E | B | DERIVED_CORRESPONDENCE | 0 | NO |
| pair_004 | 20200229T0938004033 | South_Polar_43E | B | DERIVED_CORRESPONDENCE | 0 | NO |
| pair_005 | 20200824T0806596861 | Southern_56E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_006 | 20200824T1003365280 | Southern_56E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_007 | 20200825T1322594314 | Southern_39E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_008 | 20200825T1716291272 | Southern_39E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_009 | 20200826T0459464752 | Southern_31E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_010 | 20200826T0853204550 | Southern_31E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_011 | 20200827T0030107497 | South_Polar_20E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_012 | 20200827T0226453039 | South_Polar_20E_USGS | B | GEOREFERENCED_REFERENCE | 36 | YES (LOLA) |
| pair_013 | 20200827T0423073950 | South_Polar_20E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_014 | 20200827T0619368134 | South_Polar_20E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_015 | 20190906T1246532096 | Equatorial_South_70E | C | DERIVED_CORRESPONDENCE | 0 | NO |
| pair_016 | 20210331T2033243734 | Mid_South_41E | C | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_017 | 20210401T2200364910 | Mid_South_25E | C | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_018 | 20210401T2357376656 | Mid_South_25E | C | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_019 | 20210405T0442095110 | South_Polar_341E | B | DERIVED_CORRESPONDENCE | 36 | NO |
| pair_020 | 20210405T0640233469 | South_Polar_341E | B | DERIVED_CORRESPONDENCE | 36 | NO |

*Pairs 003, 004, and 015 have 0 control points because the current reference-footprint model does not yield a geographic intersection. Pairs 016-018 each have a 6×6 derived grid but remain Quality C because their overlap is inferred, not independently confirmed.*

---

## Control-Point Inventory

- **Total derived points:** 612
- **Points per pair (where overlap confirmed):** 36 (6×6 grid)
- **Coordinate system:** Selenographic IAU2015 (geographic) + OHRC image pixel (derived)
- **TMC-2 pixel coordinates:** UNKNOWN — TMC-2 image dimensions not available in source CSV
- **Verification method:** `geospatially_derived` for ALL points
- **Grid layout:** 6×6 regular grid within OHRC/TMC-2 intersection bounding box

### Spatial Distribution

Points are distributed on a 6×6 grid spanning the full intersection region — intentionally avoiding concentration around crater rims or texture-rich spots. Grid spacing is approximately equal in latitude and longitude.

---

## Independent References

| Reference | Pairs | Notes |
|-----------|-------|-------|
| LOLA DEM (LDEM_60S_120M) | pair_012 | Independent lunar reference. ~20°E south polar region. NOT pixel-level GT. |
| LOLA DEM (LDEM_75S) | pair_012 | Higher resolution LOLA polar DEM for same region |
| USGS/ASP documentation | pair_012 | Explicitly names OHRC and TMC-2 product IDs |

All other pairs: `independent_reference = NO`

---

## Coordinate Systems

| System | Used for |
|--------|---------|
| Selenographic IAU2015 | All geographic coordinates (lat/lon) |
| OHRC image pixel (0-based, top-left origin) | source_x, source_y in control point CSVs |
| TMC-2 image pixel | NOT AVAILABLE — image dimensions unknown |

---

## Accuracy Information

| Level | Available | Notes |
|-------|-----------|-------|
| Sub-degree geographic | YES | Corner coordinates from OHRC metadata |
| Meter-level geographic | YES | OHRC pixel resolution × pixel position |
| Pixel-level registration | NO | No manually verified correspondences |
| Sub-pixel registration | NO | No independently verified sub-pixel data |

**What can be claimed:**
- Geographic position accuracy: ~OHRC pixel resolution × image position error ≈ order of magnitude 1–10m
- OHRC pixel coordinate accuracy: depends on corner coordinate accuracy (claimed ~0.25m GSD but geolocation may have larger error)
- TMC-2 pixel accuracy: NOT DETERMINABLE without TMC-2 image dimensions

---

## Spatial Coverage

| Region | Latitude | Longitude | # Pairs | Epoch |
|--------|----------|-----------|---------|-------|
| South Polar 41°E | -68 to -69°S | 41–42°E | 2 | 2020-08 |
| South Polar 43°E | -73 to -74°S | 42–44°E | 2 | 2020-02 |
| Southern 56°E | -61 to -62°S | 56–57°E | 2 | 2020-08 |
| Southern 39°E | -63 to -64°S | 39–40°E | 2 | 2020-08 |
| Southern 31°E | -65 to -67°S | 31–32°E | 2 | 2020-08 |
| South Polar 20°E | -64 to -69°S | 20–21°E | 4 | 2020-08 |
| Equatorial S 70°E | -14 to -17°S | 69–71°E | 1 | 2019-09 |
| Mid-South 41°E | -19 to -21°S | 41–42°E | 1 | 2021-03 |
| Mid-South 25°E | -12 to -14°S | 25°E | 2 | 2021-04 |
| South Polar 341°E | -68 to -69°S | 341°E (-19°W) | 2 | 2021-04 |

---

## Known Limitations

1. **Images not downloaded.** PRADAN login required. All pixel data is coordinate-derived only.
2. **TMC-2 image dimensions unknown.** TMC-2 pixel coordinates cannot be computed. `reference_x/reference_y = UNKNOWN` in all control point CSVs.
3. **No manually verified correspondences.** Zero manually annotated pixel pairs. All 612 CPs are geospatially derived.
4. **No sub-pixel ground truth.** The dataset cannot currently support sub-pixel validation claims.
5. **Same-mission georeferencing.** OHRC and TMC-2 share mission-level coordinate systems — not fully independent.
6. **6 unique TMC-2 scenes only.** IIT team confirmed 18 OHRC/TMC pairs from 6 TMC scenes — pairs in the same group share the same TMC reference image.
7. **Inferred pairs (pair_015 to pair_018).** Overlap not confirmed by running IIT overlap script. Quality C.
8. **IIT team's primary goal was super-resolution, not registration.** Their coordinate mapping served a different purpose.

---

## Recommended MVP Validation Set

### Demonstration pair (Pair A):
**pair_001** — South Polar 41°E, quality B, 36 derived CPs, IIT + USGS/ASP documented region.

### Independent validation pair (Pair B):
**pair_012** — South Polar 20°E, quality B, GEOREFERENCED_REFERENCE, LOLA independent reference. Strongest scientific backing.

### Difficult/robustness pair (Pair C):
**pair_003** — South Polar 43°E at -73 to -74°S. Extreme latitude, very low solar elevation, high shadow fraction, low texture. Expected challenge for SIFT.

---

## What Can Legitimately Be Claimed

✅ "We identified 20 OHRC ↔ TMC-2 image pairs with documented geographic overlap."
✅ "We derived 612 geospatially-interpolated reference correspondences from corner coordinate metadata."
✅ "pair_012 has an external LOLA reference independent of Chandrayaan-2."
✅ "Our synthetic validation set provides exact pixel-level GT for 5 transformation types."
✅ "The dataset covers 10 distinct lunar regions spanning 2019–2021."

---

## What Cannot Legitimately Be Claimed

❌ "We have manually verified pixel correspondences."
❌ "Our control points have sub-pixel accuracy."
❌ "Our reprojection error equals registration accuracy."
❌ "TMC-2 pixel coordinates have been validated."
❌ "The dataset provides independent ground truth" — only pair_012 has any independence.

---

## Reproduction Instructions

```bash
# 1. Clone IIT repository (source coordinate data)
git clone https://github.com/jha04amartya/ISRO-InterIIT-Techmeet-11.0

# 2. Source CSVs are already saved in:
ground_truth/sources/coordinates_ohrc_iit.csv
ground_truth/sources/coordinates_tmc2_iit.csv

# 3. Rebuild dataset from scratch
cd ground_truth/sources
python build_dataset.py

# 4. Download actual images (requires ISRO PRADAN account)
# Visit: https://pradan.issdc.gov.in/ch2/
# Search for product IDs listed in manifests/pairs.csv
# Place in corresponding pairs/pair_NNN/raw/ directories

# 5. For LOLA independent reference (pair_012)
# Download LDEM_60S_120M from: https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
# Clip to region: 67-71°S, 19-22°E

# 6. To obtain exact TMC-2 product IDs (currently listed as provisional):
# Run: ground_truth/sources/coordinates_tmc2_iit.csv through IIT overlap script
# (ohrc_tmc_overlap.py in the IIT repository)
# This will identify the 6 unique TMC-2 scenes that match the 18 OHRC pairs
```

---

*Dataset assembled by Team Avishkar for SIH26166. Build date: 2026-08-31.*
