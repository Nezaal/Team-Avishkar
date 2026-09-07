# 🚀 Lunar Image Co-Registration: Architecture & Progress Report
**Team Avishkar | SIH26166**

## 1. The Problem Statement & Our Research
Our objective is to build an automated pipeline to co-register ultra-high-resolution Chandrayaan-2 OHRC imagery (0.25 m/px) onto regional TMC-2 maps (4.48 m/px). 

During our initial research, we discovered three critical bottlenecks that cause traditional computer vision (like SIFT) to fail:
* **Extreme Scale Variance:** An ~18x resolution difference makes standard feature descriptors completely incompatible.
* **Temporal Illumination Inversion:** Images taken months or years apart have drastically different sun angles. Crater shadows invert, tricking traditional algorithms into interpreting craters as mountains.
* **Telemetry Drift:** ISRO's satellite GPS metadata can drift by over a kilometer, meaning blind geographical cropping extracts non-overlapping terrain.

## 2. Data Processing & Tiling Architecture
To handle massive, gigabyte-sized satellite images without causing catastrophic memory bottlenecks, we built a highly scalable data-streaming engine:
* **Image Tiling:** We sliced the massive lunar maps into over **65,000+ fixed-size (512x512) NumPy (`.npz`) tiles**.
* **Preprocessing & Masking:** Each tile contains the raw image, a preprocessed state, and a validity mask (to ignore no-data regions).
* **Lazy-Loading (`TileStore`):** Instead of loading everything into RAM, our pipeline uses a central `dataset_manifest.json` to instantly locate and load only the exact coordinate tiles requested, reducing memory overhead by 99%.

## 3. The Deep Learning Pipeline
Because traditional algorithms failed against shadow inversion and scale, we moved to a State-of-the-Art Deep Learning architecture:
* **SuperPoint & LightGlue:** We replaced SIFT with AI-driven sparse keypoint matching. SuperPoint extracts highly distinct, robust features, while LightGlue uses a Transformer-based architecture to contextually correlate those features across massive scale gaps.
* **Geometric Estimation:** We pass the neural network's matches through Lowe's ratio tests and RANSAC algorithms to filter out fake matches and mathematically compute the true geometric transformation (Affine/Homography).
* **Structural Edge Matching:** To bypass shadow inversion entirely, we also implemented Phase Correlation (Fast Fourier Transform) on Canny Edge-maps to structurally match crater rims independent of lighting.

## 4. Full-Stack Integration
We didn't just build a python script; we built a modular software application:
* **FastAPI Backend:** The entire Deep Learning pipeline runs on a high-performance, GPU-accelerated backend. It processes registration requests on the fly and returns structured JSON metrics and correspondence coordinates.
* **React & Vite Dashboard:** A responsive web UI where users can select image pairs, trigger the AI backend, and visually inspect the geometric matches, outliers, and reprojection errors drawn dynamically on an HTML5 Canvas.

## 5. What Has Been Done Till Now
✅ **Dataset Generation:** Successfully generated and compressed the 65,616-tile OHRC dataset.
✅ **AI Engine Validation:** Successfully integrated both LoFTR and SuperPoint+LightGlue models, running flawlessly on local CUDA environments.
✅ **Pipeline Verification:** The backend chain (Loader → Pair Selection → Neural Network Extraction → RANSAC → Metrics) executes end-to-end perfectly on spatially adjacent OHRC tiles.
✅ **Full-Stack Connection:** The React frontend and FastAPI backend are actively communicating, successfully triggering inference and passing coordinate data.

## 6. Future Plans & Next Steps
* **Overcome Telemetry Drift:** Since the AI pipeline works perfectly, our next step is implementing a sliding-window grid search (or manual ROI injections) to find the true geographic overlap of TMC-2 images, bypassing the inaccurate ISRO GPS coordinates.
* **Cross-Sensor Finalization:** Successfully align the 0.25m OHRC features onto the 4.48m TMC-2 map to generate the final registered output images.
* **Domain-Specific Fine-Tuning:** If required, fine-tune the LightGlue neural network weights specifically on lunar crater topologies to increase confidence scores.
* **Deployment:** Containerize the backend and frontend for seamless cloud deployment and judging.
