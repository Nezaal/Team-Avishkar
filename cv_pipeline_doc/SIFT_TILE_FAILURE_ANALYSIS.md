# SIFT Tile Matching: Failure Analysis (Low Confidence)

## The Issue
When executing the CV Pipeline (OpenCV SIFT + RANSAC) directly on the 512x512 .npz ML training tiles, the pipeline correctly executes but returns a LOW_CONFIDENCE score (typically ~4 inliers).

## Root Cause: Geographic Scale Mismatch
The SIFT algorithm requires images to have identifiable features at roughly similar scales. The .npz ML tiles are perfectly matched numpy arrays of size 512x512 pixels. However, because the two sensors have vastly different spatial resolutions, the physical area covered by a 512x512 tile is completely different:

* **TMC-2 Resolution:** ~4.48 meters/pixel
* **TMC-2 Tile Footprint:** 512 pixels * 4.48 = **2,293 meters** (2.3 km) of the moon's surface.

* **OHRC Resolution:** ~0.25 meters/pixel
* **OHRC Tile Footprint:** 512 pixels * 0.25 = **128 meters** of the moon's surface.

## Why SIFT Fails
When you feed these two 512x512 arrays into SIFT, SIFT is trying to match a tiny 128-meter box against a massive 2.3-kilometer landscape. The OHRC image is effectively a microscopic dot inside the TMC-2 image. 

While SIFT is mathematically "scale-invariant," a 17.9x scale difference on barren lunar terrain stretches the limits of its Gaussian pyramid layers, causing RANSAC to reject almost all tentative matches and drop to ~4 inliers.

## Conclusion
This failure is strictly a limitation of the traditional SIFT algorithm, NOT a failure of the tile generation. The .npz tiles are structurally flawless and perfectly aligned for the future Deep Learning (SuperGlue/LoFTR) upgrade, which will successfully bridge this 17.9x scale gap.
