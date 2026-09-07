# Frontend Dashboard Implementation Plan

Based on the architectural requirements and the visual reference design, this document outlines the precise layout, components, and data flow for the Computer Vision Demo Dashboard.

---

## 1. Dashboard Layout & UI Components
The dashboard follows a 2-row, 5-panel layout designed to provide maximum visual proof of the pipeline's sub-pixel accuracy without requiring the user to download raw data.

### Row 1: Visual Proof
**Panel 1: Image Pair Preview (Top Left)**
*   **Inputs:** Two dropdown menus ("Source Image: OHRC" and "Reference Image: TMC-2") populated automatically from pairs.csv. 
*   **Action Button:** A button to execute the pipeline on the selected pair.
*   **Visualization:** An OpenCV drawMatches image showing the OHRC and TMC-2 images side-by-side with colorful lines connecting the extracted SIFT keypoints.
*   **Metadata:** Labels beneath each image showing the working resolution and GSD (e.g., 1024 x 1024 • 0.25 m/px).

**Panel 2: Registration Result (Top Right)**
*   **Visualization:** An interactive "Image Comparison Slider" (Before/After). The user can drag the slider left and right to see the OHRC image perfectly warped and overlaid onto the TMC-2 image.
*   **Status Banner:** A dynamic colored banner at the bottom (e.g., Green: Registration Successful, Red: Low Confidence).

### Row 2: Mathematical Proof (Metrics)
**Panel 3: Correspondence Distribution (Bottom Left)**
*   **Visualization:** A 2D Scatter Plot grid representing the image coordinates. 
*   **Data Source:** Plotted using the ohrc_raw_x and ohrc_raw_y arrays returned by the API.
*   **Purpose:** Proves to the judges that the matching points are "Well Distributed" across the whole image rather than concentrated in one single corner.

**Panel 4: Reprojection Error (Bottom Middle)**
*   **Visualization:** A Histogram Bar Chart.
*   **Data Source:** Bins the individual pixel errors of the RANSAC inliers.
*   **Purpose:** Visually proves sub-pixel accuracy. Shows a bell curve peaking underneath the 1.0 px mark, with a dotted line indicating the Mean RMSE (e.g., Mean: 0.38 px).

**Panel 5: Transformation Summary (Bottom Right)**
*   **Visualization:** A clean, formatted table.
*   **Data Source:** Displays the exact 3x3 Homography Matrix returned by the API, the total Inlier fraction (e.g., 12,387 / 18,642), and the final Reprojection Error.

---

## 2. Data Flow & Backend Integration

To make this dashboard lightning-fast for a live demo:

1. **User Selects Pair:** User clicks a pair in the Top-Left dropdown.
2. **FastAPI Request:** The frontend sends a GET /pipeline/pair/{id} request to the backend.
3. **Backend Magic:** 
    * The backend uses ead_remote_window() to fetch a 1024x1024 chunk directly from the Hugging Face CDN (bypassing the 3GB .img file).
    * It runs the SIFT/RANSAC pipeline.
    * It uses cv2.drawMatches to generate the Match Image (Panel 1) and cv2.warpPerspective to generate the Aligned Image (Panel 2), saving them as .png files in a static/ cache.
4. **Dashboard Render:** The backend returns the .png URLs and the JSON metrics. The frontend updates the Scatter Plot (Panel 3), Histogram (Panel 4), and Matrix Table (Panel 5).

---

## 3. Recommended Tech Stack
*   **Frontend Framework:** Streamlit (Python) or React/Next.js. Streamlit is highly recommended for ML teams as it natively supports matplotlib scatter plots, histograms, and image comparison sliders in pure Python.
*   **Backend:** FastAPI (Already built).
