"""
ChandraMatch FastAPI Server (Module B8 API Integration)

Provides REST endpoints for:
- GET /health: Health check
- GET /dataset/info: Dataset metadata summary
- GET /pipeline/pair: Complete B2-B8 pipeline execution on 1 tile pair
- GET /pipeline/sample: Deterministic B3 pair selection + B2-B8 pipeline execution on 1 tile pair
"""
import os
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.runner import PipelineRunner

app = FastAPI(
    title="ChandraMatch Image Processing API",
    description="Backend API for Chandrayaan-2 lunar image registration & feature matching pipeline",
    version="1.0.0",
)

# Shared runner instance
runner = PipelineRunner()


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")


@app.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/dataset/info")
def get_dataset_info():
    """Return OHRC dataset metadata summary (read-only metadata, zero array loading)."""
    try:
        return runner.get_dataset_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/pair")
def run_pipeline_pair(
    tile_a_id: str = Query(..., description="Reference Tile A ID"),
    tile_b_id: str = Query(..., description="Moving Tile B ID"),
    split: Optional[str] = Query(None, description="Dataset split (train/val/test)"),
):
    """Run full B2-B8 pipeline on ONE requested tile pair."""
    try:
        result = runner.run_pair(tile_a_id=tile_a_id, tile_b_id=tile_b_id, split=split)
        status_code = result.get("status")
        if status_code == "TILE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.get("message", "Tile not found"))
        if status_code in ("CROSS_SPLIT_PROHIBITED", "CROSS_PRODUCT_PROHIBITED"):
            raise HTTPException(status_code=400, detail=result.get("message", "Invalid pair request"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")


@app.get("/pipeline/sample")
def run_pipeline_sample(
    split: str = Query("train", description="Dataset split: train, val, or test"),
    mode: str = Query("adjacent", description="Pair mode: adjacent, overlap, or all"),
):
    """Use B3 to deterministically select ONE tile pair and run the complete B2-B8 pipeline."""
    try:
        if split.lower().strip() not in ("train", "val", "test"):
            raise HTTPException(status_code=400, detail=f"Invalid split '{split}'. Must be 'train', 'val', or 'test'.")
        result = runner.run_selected_pair(split=split, mode=mode)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample pipeline error: {str(e)}")
