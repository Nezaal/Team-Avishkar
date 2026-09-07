"""FastAPI service for the LoFTR baseline; run with uvicorn backend.loftr_api:app."""
from pathlib import Path
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from loftr_pipeline.data import TileStore
from loftr_pipeline.pipeline import ROOT, RunConfig, run

app = FastAPI(title="ChandraMatch LoFTR API", version="1.0")
RUN_ROOT = ROOT / "dataset" / "loftr_runs"
RUN_ROOT.mkdir(parents=True, exist_ok=True)
RUN_LOCK = threading.Lock()


class RegistrationRequest(BaseModel):
    pair_id: str = "pair_001"
    source_roi: list[int] | None = None
    reference_roi: list[int] | None = None
    source_side: int = Field(default=8192, ge=1024, le=12000)
    max_size: int = Field(default=640, ge=128, le=1024)
    model: Literal["affine", "homography"] = "affine"
    min_confidence: float = Field(default=.5, ge=0, le=1)
    ransac_threshold: float = Field(default=2., gt=0, le=10)
    clahe: bool = False
    device: Literal["auto", "cpu", "cuda"] = "auto"

    @model_validator(mode="after")
    def validate_rois(self):
        for roi in (self.source_roi, self.reference_roi):
            if roi is not None and (len(roi) != 4 or min(roi[:2]) < 0 or min(roi[2:]) <= 0):
                raise ValueError("ROI must be [x, y, width, height]")
        if self.reference_roi and not self.source_roi:
            raise ValueError("reference_roi requires source_roi")
        return self


@app.get("/health")
def health():
    return {"status": "ok", "method": "pretrained_loftr_outdoor"}


@app.get("/pairs")
def pairs():
    try:
        store = TileStore()
        return {"pairs": store.available_pairs(), "revision": store.revision}
    except Exception as exc:
        raise HTTPException(503, f"Dataset manifest unavailable: {exc}") from exc


@app.post("/register")
def register(request: RegistrationRequest):
    # One process/GPU inference at a time. Deploy multiple workers only with separate GPU assignment.
    with RUN_LOCK:
        result = run(RunConfig(**request.model_dump(), output_root=str(RUN_ROOT)))
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
    if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
        raise HTTPException(404, "Run not found")
    if Path(name).name != name or name not in {"result.json", "report.html", "source.png", "reference.png", "matches.png", "tentative_matches.png", "registered.png", "valid_overlap.png", "overlay.png", "checkerboard.png", "correspondences.csv", "transform.json", "registered_tmc2_native_roi.png", "reference_tmc2_native_roi.png", "registered_tmc2_native_mask.png"}:
        raise HTTPException(404, "Artifact not found")
    return RUN_ROOT / run_id / name
