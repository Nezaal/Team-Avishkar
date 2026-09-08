# 🌕 ChandraMatch: Lunar Image Co-Registration Pipeline
**Team Avishkar | Smart India Hackathon (SIH26166)**

ChandraMatch is an enterprise-grade, state-of-the-art computer vision pipeline built to solve the extreme challenges of registering ultra-high-resolution Chandrayaan-2 OHRC imagery (0.25 m/px) with regional TMC-2 imagery (4.48 m/px).

## 🚀 The Challenge
Registering satellite imagery across these two sensors is incredibly difficult due to:
1. **Extreme Scale Variance:** An 18x resolution difference makes traditional feature matching nearly impossible.
2. **Temporal Illumination Inversion:** Images taken months or years apart have drastically different sun angles, causing crater shadows to invert (tricking algorithms like SIFT into thinking craters are mountains).
3. **Telemetry Drift:** Satellite GPS bounding boxes can drift by kilometers, requiring robust structural searching rather than blind geographic alignment.

## 🧠 Our Solution
We discarded outdated traditional CV techniques and built a **Deep Learning & FFT-powered pipeline**:
* **AI Feature Matching:** Utilizing **SuperPoint** for highly robust, sparse keypoint extraction, and **LightGlue** for context-aware feature correlation.
* **Illumination Invariance:** Implementing Fast Fourier Transform (FFT) Phase Correlation on Canny Edge Maps to match physical crater structures completely independent of shadow direction.
* **Massive Scale Data Handling:** A custom `TileStore` engine that lazy-loads from a local streaming dataset of over **65,000+ compressed `.npz` tiles**, eliminating RAM bottlenecks.

## 🏗️ System Architecture
The project is divided into a high-performance backend processing engine and an interactive frontend dashboard.

### Tech Stack
* **AI/CV Engine:** PyTorch, LightGlue, OpenCV, SciPy
* **Backend:** FastAPI, Uvicorn, Python
* **Frontend:** React, Vite, HTML5 Canvas
* **Data Layer:** NumPy (`.npz`), Pandas

## 💻 How to Run & Test the Demo

### 1. Start the AI Backend Engine (FastAPI)
The backend dynamically executes the selected computer vision algorithm (SIFT, LoFTR, or LightGlue) and serves the resulting geometric transformations.

```bash
# From the project root directory
python backend\main.py
```
*(The backend will start on `http://127.0.0.1:8001`)*

### 2. Start the Frontend Dashboard (React)
The frontend provides a beautiful, interactive Before/After comparison slider and metric visualizations.

```bash
# In a new terminal
cd dashboard
npm install
npm run dev
```
*(The frontend will start on `http://localhost:3000`)*

### 3. Test the Dashboard
1. Open [http://localhost:3000](http://localhost:3000) in your web browser.
2. Select your desired algorithm (**SIFT**, **LoFTR**, or **LightGlue**) from the Pipeline Configuration dropdown.
3. Click the **Run Pipeline** button.
4. Wait for the algorithm to process (SIFT takes ~2 seconds, Deep Learning models like LoFTR take ~15 seconds).
5. Explore the interactive Before/After overlay slider, correspondence distribution, and reprojection error metrics!

## 🌐 How to Expose for Remote Presentations (Optional)
If you need to share your localhost dashboard securely during a live presentation without dealing with CORS or network blocks, you can run Pinggy in a third terminal:

```bash
ssh -p 443 -R0:localhost:3000 a.pinggy.io
```
This will instantly generate a public URL that tunnels both the frontend UI and backend API!

## 📊 Project Status
* ✅ End-to-end data preprocessing (65,000+ tiles generated)
* ✅ Deep Learning Pipeline (SuperPoint + LightGlue) integrated and GPU-accelerated
* ✅ FastAPI Backend and React Dashboard wired and communicating locally
* 🔄 **Next Steps:** Applying the validated pipeline to manually corrected TMC-2 ROIs to finalize the cross-sensor mapping outputs.
