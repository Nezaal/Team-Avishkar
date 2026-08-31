# Technical Questions & Decisions

## Open Questions

1. **TMC-2 Product Identification**
   - *Question:* What are the exact TMC-2 product IDs used by the IIT team?
   - *Context:* The IIT team identified 18 OHRC overlapping pairs from 6 unique TMC-2 scenes, but their CSV contains 1,083 records and does not explicitly list the 6 chosen IDs.
   - *Next Step:* Run the `ohrc_tmc_overlap.py` script from the IIT repo against `coordinates_tmc2_iit.csv` to recover the exact 6 IDs.

2. **TMC-2 Pixel Coordinates**
   - *Question:* How do we compute the TMC-2 pixel coordinates (reference_x, reference_y) for our control points?
   - *Context:* The IIT `coordinates_tmc2.csv` does not include `shape_x` and `shape_y` (image dimensions) for the TMC-2 records, preventing bilinear interpolation into pixel space.
   - *Next Step:* Wait until the raw TMC-2 images are downloaded via PRADAN to obtain their exact dimensions, then re-run the `build_dataset.py` script.

3. **Sub-pixel Validation**
   - *Question:* How will we validate sub-pixel accuracy claims?
   - *Context:* All 612 current control points are `geospatially_derived` from corner coordinate interpolation. They are not manually verified and cannot support sub-pixel claims.
   - *Next Step:* CV team needs to manually annotate ~30 pixel-exact correspondences for at least the MVP Pair A, B, and C.

## Resolved Decisions

1. **Dataset Scope**
   - *Decision:* Build a pure data engineering dataset (20 pairs, metadata, scripts) without running any CV pipeline code.
   - *Rationale:* Follows strict instruction: "Your ONLY task is to research, scrape, download, extract, normalize, and organize ground-truth/reference data... DO NOT build the CV pipeline."

2. **Control Point Provenance**
   - *Decision:* Explicitly label all 612 derived control points with `verification_method = geospatially_derived` and `accuracy = sub-degree_geographic_only`.
   - *Rationale:* Prevents false claims of sub-pixel accuracy. The points are mathematically interpolated from corner metadata, not manually measured.

3. **Independent Reference**
   - *Decision:* Identify pair_012 as the sole `GEOREFERENCED_REFERENCE` pair, backed by LOLA DEM data via USGS/ASP documentation.
   - *Rationale:* Provides at least one pair with a documented, independent (non-Chandrayaan-2) reference source for robust validation.
