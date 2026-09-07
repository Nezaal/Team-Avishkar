"""FastAPI service for the SuperPoint + LightGlue baseline; run with uvicorn backend.lightglue_api:app."""
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from loftr_pipeline.data import TileStore
from loftr_pipeline.pipeline import ROOT, RunConfig
from loftr_pipeline.lightglue import run_lightglue

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ChandraMatch LightGlue API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUN_ROOT = ROOT / "dataset" / "lightglue_runs"
RUN_ROOT.mkdir(parents=True, exist_ok=True)
RUN_LOCK = threading.Lock()

class RegistrationRequest(BaseModel):
    pair_id: str = "pair_001"
    source_roi: list[int] | None = None
    reference_roi: list[int] | None = None
    source_side: int = Field(default=8192, ge=1024, le=12000)
    max_size: int = Field(default=512, ge=128, le=1024)
    model: Literal["affine", "homography"] = "affine"
    min_confidence: float = Field(default=.5, ge=0, le=1)
    ransac_threshold: float = Field(default=5., gt=0, le=10)
    clahe: bool = False
    device: Literal["auto", "cpu", "cuda"] = "cuda"
    local_root: str = "."
    cache_dir: str = "C:/hfcache"

    @model_validator(mode="after")
    def validate_rois(self):
        for roi in (self.source_roi, self.reference_roi):
            if roi is not None and (len(roi) != 4 or min(roi[:2]) < 0 or min(roi[2:]) <= 0):
                raise ValueError("ROI must be [x, y, width, height]")
        return self

@app.get("/health")
def health():
    return {"status": "ok", "method": "superpoint_lightglue"}

@app.get("/pairs")
def pairs():
    try:
        store = TileStore(local_root=".", offline=True)
        return {"pairs": store.available_pairs(), "revision": store.revision}
    except Exception as exc:
        raise HTTPException(503, f"Dataset manifest unavailable: {exc}") from exc

@app.post("/register")
def register(request: RegistrationRequest):
    with RUN_LOCK:
        cfg = RunConfig(**request.model_dump(), output_root=str(RUN_ROOT), offline=True)
        result = run_lightglue(cfg)
    return result

@app.get("/runs/{run_id}")
def result(run_id: str):
    path = _path(run_id, "result.json")
    if not path.is_file():
        raise HTTPException(404, "Run not found")
    return FileResponse(path, media_type="application/json")

@app.get("/runs/{run_id}/artifacts/{name}")
def artifact(run_id: str, name: str):
    path = _path(run_id, name)
    if not path.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(path)

def _path(run_id: str, name: str):
    if not run_id.startswith("lg_") or len(run_id) != 32:
        raise HTTPException(404, "Run not found")
    valid_artifacts = {
        "result.json", "report.html", "source.png", "reference.png", "matches.png",
        "correspondences.csv", "registered.png", "valid_overlap.png", "overlay.png",
        "checkerboard.png", "tentative_matches.png", "transform.json",
        "registered_tmc2_native_roi.png", "reference_tmc2_native_roi.png",
        "registered_tmc2_native_mask.png",
    }
    if name not in valid_artifacts:
        raise HTTPException(404, "Artifact not found")
    return RUN_ROOT / run_id / name
