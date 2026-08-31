# SIH26166 Engineering Flow

## Overview
This document tracks the current development flow for the SIH26166 MVP.

## Current Stage: Data Engineering (Ground Truth Collection)
**Status:** In Progress (Dataset structure built, data acquisition pending PRADAN access)

1. **Scoping & Setup [DONE]**
   - Read SRD, PRD, AGENT.md
   - Identify sources (IIT repo, USGS/ASP, PRADAN, LOLA)

2. **Data Scraping & Extraction [DONE]**
   - Downloaded OHRC and TMC-2 metadata from IIT repository
   - Extracted 25 OHRC scenes
   - Extracted inferred TMC-2 scenes

3. **Dataset Structure Generation [DONE]**
   - Generated `ground_truth/` directory tree
   - Built 20 OHRC ↔ TMC-2 pair directories
   - Created control point CSVs using bilinear geographic interpolation
   - Built manifest and validation CSVs

4. **Image Data Acquisition [PENDING]**
   - Download OHRC `.img` files from PRADAN
   - Download TMC-2 `.img` files from PRADAN

5. **Validation & Finalization [PENDING]**
   - Determine exact TMC-2 product IDs via `ohrc_tmc_overlap.py`
   - Recompute TMC-2 pixel coordinates once image dimensions are known
   - Manually annotate ~30 pixel-level control points for Pairs A, B, C

## Next Stage: CV Pipeline (Future)
- SIFT / SuperGlue implementation
- Homography estimation (RANSAC)
- Validation against ground truth dataset
