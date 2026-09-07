import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.runner import PipelineRunner
from pipeline.cv_pipeline import register_images

app = FastAPI(title="ChandraMatch CV API")
runner = PipelineRunner()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ChandraMatch CV API"}

@app.get("/pipeline/pair/{pair_id}")
def run_pipeline(pair_id: str):
    try:
        prep_result = runner.run_preprocessing(pair_id)
        
        cv_result = register_images(
            source_prep=prep_result["source_preprocessed"], 
            reference_prep=prep_result["reference_preprocessed"],
            pair_meta=prep_result["pair"]
        )
        
        if cv_result["status"] == "FAILED":
            return {"pair_id": pair_id, "status": "FAILED", "reason": cv_result["reason"]}
            
        return {
            "pair_id": pair_id,
            "status": cv_result["status"],
            "metrics": cv_result["metrics"],
            "transformation_matrix": cv_result["transformation_matrix"],
            "total_correspondences": len(cv_result["correspondences"]),
            "sample_correspondences": cv_result["correspondences"][:5]
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pair {pair_id} not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
