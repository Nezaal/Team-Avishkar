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

## 💻 How to Run

### 1. Start the AI Backend (FastAPI)
The backend runs the Deep Learning inference on your GPU and serves the results via REST API.
```bash
# From the root directory
uvicorn backend.lightglue_api:app --host 0.0.0.0 --port 8002
```

### 2. Start the Frontend Dashboard (React)
The frontend provides a beautiful, interactive visualizer for the geometric correspondences.
```bash
# In a new terminal
cd dashboard
npm install
npm run dev
```
Open `http://localhost:3000` in your browser and click **Run Co-Registration**.

## 📊 Project Status
* ✅ End-to-end data preprocessing (65,000+ tiles generated)
* ✅ Deep Learning Pipeline (SuperPoint + LightGlue) integrated and GPU-accelerated
* ✅ FastAPI Backend and React Dashboard wired and communicating locally
* 🔄 **Next Steps:** Applying the validated pipeline to manually corrected TMC-2 ROIs to finalize the cross-sensor mapping outputs.
