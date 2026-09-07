from fastapi import FastAPI, HTTPException
import uvicorn
import sys, os, json, cv2
import numpy as np
import urllib.request
from io import BytesIO

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.cv_pipeline import register_images
from config import get_huggingface_config, get_local_storage_config

app = FastAPI(title="ChandraMatch CV API - Tile Engine")

def get_remote_npz(url: str, token: str = None) -> bytes:
    req = urllib.request.Request(url)
    if token and token != "YOUR_HF_TOKEN":
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15.0) as response:
            return response.read()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

@app.get("/api/pipeline/run_tiles/{ohrc_tile_id}/{tmc2_tile_id}")
async def run_pipeline_on_tiles(ohrc_tile_id: str, tmc2_tile_id: str):
    """
    Executes the SIFT CV Pipeline directly on two pre-generated .npz ML tiles.
    Uses the 'preprocessed' arrays directly from the .npz files.
    """
    hf_config = get_huggingface_config()
    local_config = get_local_storage_config()
    
    use_remote_first = hf_config.get("use_remote_first", True)
    hf_token = hf_config.get("api_key", None)
    base_remote = hf_config.get("dataset_base_url", "https://huggingface.co/datasets/akshitjn/my-large-dataset/resolve/main/")
    local_base = local_config.get("ml_tiles_path", "dataset/streaming_dataset/tiles/")

    ohrc_product = ohrc_tile_id.split("__")[0]
    tmc2_product = tmc2_tile_id.split("__")[0]

    ohrc_array = None
    ohrc_mask = None
    tmc2_array = None
    tmc2_mask = None
    source_used = "None"
    
    # 1. TRY HUGGING FACE FIRST
    if use_remote_first:
        print("Attempting to fetch .npz tiles from Hugging Face...")
        ohrc_url = base_remote + f"streaming_dataset/tiles/{ohrc_product}/{ohrc_tile_id}.npz"
        tmc2_url = base_remote + f"streaming_dataset/tiles/{tmc2_product}/{tmc2_tile_id}.npz"
        
        ohrc_bytes = get_remote_npz(ohrc_url, hf_token)
        tmc2_bytes = get_remote_npz(tmc2_url, hf_token)
        
        if ohrc_bytes and tmc2_bytes:
            try:
                with np.load(BytesIO(ohrc_bytes)) as data:
                    ohrc_array = data['preprocessed']
                    ohrc_mask = data['mask']
                with np.load(BytesIO(tmc2_bytes)) as data:
                    tmc2_array = data['preprocessed']
                    tmc2_mask = data['mask']
                source_used = "Hugging Face"
                print("Successfully loaded .npz tiles from Hugging Face.")
            except Exception as e:
                print(f"Failed to parse remote .npz file: {e}")
                ohrc_array = None
                tmc2_array = None

    # 2. FALLBACK TO LOCAL STORAGE
    if ohrc_array is None or tmc2_array is None:
        print(f"Falling back to local storage in {local_base}...")
        local_ohrc_path = os.path.join(BACKEND_DIR, "..", local_base, ohrc_product, f"{ohrc_tile_id}.npz")
        local_tmc2_path = os.path.join(BACKEND_DIR, "..", local_base, tmc2_product, f"{tmc2_tile_id}.npz")
        
        if not os.path.exists(local_ohrc_path) or not os.path.exists(local_tmc2_path):
            raise HTTPException(status_code=404, detail="Tiles not found remotely or locally.")
            
        try:
            with np.load(local_ohrc_path) as data:
                ohrc_array = data['preprocessed']
                ohrc_mask = data['mask']
            with np.load(local_tmc2_path) as data:
                tmc2_array = data['preprocessed']
                tmc2_mask = data['mask']
            source_used = "Local Storage"
            print("Successfully loaded .npz tiles from Local Storage.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Corrupted local .npz file: {e}")

    # 3. RUN SIFT CV PIPELINE
    try:
        # Pre-process arrays for OpenCV SIFT (Ensure uint8 format)
        if ohrc_array.dtype != np.uint8:
            ohrc_array = cv2.normalize(ohrc_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        if tmc2_array.dtype != np.uint8:
            tmc2_array = cv2.normalize(tmc2_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        if ohrc_mask.dtype != np.uint8:
            ohrc_mask = (ohrc_mask * 255).astype(np.uint8)
        if tmc2_mask.dtype != np.uint8:
            tmc2_mask = (tmc2_mask * 255).astype(np.uint8)

        source_prep = {"image": ohrc_array, "mask": ohrc_mask, "scale_x": 1.0, "scale_y": 1.0}
        ref_prep = {"image": tmc2_array, "mask": tmc2_mask, "scale_x": 1.0, "scale_y": 1.0, "original_height": 512}

        # Execute
        res = register_images(source_prep, ref_prep, {"tmc2_height": 512})

        return {
            "status": res.get("status", "FAILED"),
            "metrics": res.get("metrics", {}),
            "transformation_matrix": res.get("transformation_matrix", []),
            "data_source": source_used,
            "architecture": "NPZ_TILE_MATCHING"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV Pipeline failed on tile: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
