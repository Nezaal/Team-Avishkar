# SIFT Pipeline (From Scratch)

## Why We Cannot Use `.npz` Tiles With SIFT

When we ran SIFT directly on the pre-generated 512x512 `.npz` ML tiles, it returned **FAILED** (0 inliers). Here is the actual output:

```json
{
  "status": "FAILED",
  "metrics": {},
  "transformation_matrix": [],
  "data_source": "Hugging Face",
  "architecture": "NPZ_TILE_MATCHING"
}
```

### Root Cause

The `.npz` tiles are raw 512x512 pixel crops. Because the two sensors have completely different spatial resolutions, these tiles cover wildly different physical areas of the moon:

| Sensor | Resolution | 512px Tile Covers |
|--------|-----------|-------------------|
| OHRC   | 0.25 m/px | **128 meters**    |
| TMC-2  | 4.48 m/px | **2,293 meters**  |

SIFT is trying to match a tiny 128m patch against a massive 2.3km landscape. The scale difference is **17.92x**. While SIFT is theoretically "scale-invariant," a 17.92x magnification on featureless lunar regolith completely overwhelms its Gaussian pyramid, and RANSAC rejects all tentative matches.

### What The `.npz` Tiles Are Actually For

The `.npz` tiles were **never** meant for SIFT. They are the training dataset for a future Deep Learning model (SuperGlue / LoFTR) that will learn to bridge the 17.92x scale gap through neural network training.

## How This Pipeline Fixes It

This `sift_pipeline/` folder contains a completely new, standalone pipeline that:

1. **Reads real GPS coordinates** from `product_catalog.json` (Latitude/Longitude bounding boxes for each image).
2. **Calculates the exact geographic overlap** between the OHRC and TMC-2 images using their bounding boxes.
3. **Streams only the overlapping region** from the raw `.img` files on Hugging Face using HTTP Range requests.
4. **Scales the OHRC image down by the resolution ratio** (17.92x) so that craters appear at the same physical size in both images.
5. **Runs SIFT + RANSAC** on the properly aligned, properly scaled images.

Because the images now show the exact same craters at the exact same size, SIFT can find hundreds of real matches.

## Files

| File | Purpose |
|------|---------|
| `run.py` | The main executable script. Run `python sift_pipeline/run.py` |
| `README.md` | This file |
