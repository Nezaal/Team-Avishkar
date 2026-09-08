# ChandraMatch Dashboard: Output & Metrics Explanation

When you execute a pipeline (SIFT, LoFTR, or LightGlue) in the ChandraMatch dashboard, the backend calculates the geometric transformation and returns several key visual and mathematical outputs. 

Here is exactly what each section of the dashboard means, how to interpret it, and how to explain it to the judges.

---

## 1. Registration Result Box (The Visual Overlay)
This top-right panel is the core interactive centerpiece of the dashboard. It provides the ultimate visual proof that the Deep Learning pipeline has successfully aligned the two lunar surfaces. 

**What is happening behind the scenes:** The AI has calculated a 3x3 geometric transformation matrix. The backend uses this matrix to literally "warp" the pixel coordinates of the Source Image (Image A) so they overlay perfectly onto the Target Image (Image B), correcting for shift, scale, and rotation.

**How to use it during the pitch:**
* **Before/After Slider (Overlay Mode):** This is your main demonstration tool. The slider lets you dynamically wipe back and forth between the unaligned raw image and the mathematically aligned image. As you drag the slider, tell the judges to focus on a specific crater rim. They will see the crater instantly "snap" from its incorrect, shifted position into perfect pixel-perfect alignment.
* **Checkerboard Mode:** This toggles the view into a black-and-white grid pattern, alternating squares of Image A and Image B. **Why this matters:** If the registration was even slightly wrong, the crater rims would look jagged, disconnected, or broken across the grid lines. When the registration is perfect, the crater edges flow continuously and seamlessly across the alternating squares, proving the geometry is locked in.

---

## 2. Correspondence Distribution (Scatter Plot)
This scatter plot maps out exactly *where* the AI found matching features on the lunar surface. 

* **What it shows:** Every blue dot represents a perfectly matched feature (an "inlier") between the two images.
* **Why it matters:** A bad algorithm might find 500 matches, but they might all be clustered in one tiny, highly-textured corner of the image. If that happens, the transformation matrix will perfectly align that one corner but severely distort the rest of the map. 
* **The Pitch:** *"As you can see on the Correspondence Distribution plot, our algorithm successfully identified and locked onto geometric features distributed evenly across the **entire** lunar terrain, guaranteeing a mathematically sound, globally accurate transformation."*

---

## 3. Reprojection Error (Histogram)
This is the absolute mathematical proof of our accuracy. Once the AI calculates the transformation matrix, we "reproject" (mathematically warp) all the points from Image A onto Image B and measure exactly how many pixels they are off by.

* **What it shows:** The X-axis is the error distance (in pixels). The Y-axis is the number of points that had that specific error.
* **Key Metrics:**
  * **Mean/Median Error:** The average geometric distance between the matched points.
  * **P95 Error:** 95% of all matched points have an error less than this value.
* **The Pitch:** *"While the visual slider looks great, this histogram is our engineering truth. Our Median Reprojection Error is consistently under 1 pixel. This proves we are achieving true sub-pixel accuracy when aligning these massive 8192x8192 high-resolution tiles."*

---

## 4. Transformation Summary
This panel displays the raw data processing funnel, showing how the algorithm filtered down the data to find the perfect geometric fit.

* **Raw Matches:** The initial number of points the algorithm *thought* looked similar. (Usually very high, containing many false positives).
* **Filtered Matches:** The number of points left after applying confidence thresholds and spatial filtering.
* **RANSAC Inliers:** RANSAC (Random Sample Consensus) is a robust mathematical algorithm that looks at all the filtered matches and throws away the "outliers" (matches that don't fit the dominant geometric movement). The "Inliers" are the final, perfectly correct matches used to align the image.
* **Inlier Ratio:** The percentage of filtered matches that were actually correct. A higher ratio means the AI's feature matching was highly accurate before RANSAC even had to clean it up.
* **Transformation Matrix:** The actual 3x3 mathematical Affine matrix used to warp the image (handling translation, rotation, scale, and shear).
