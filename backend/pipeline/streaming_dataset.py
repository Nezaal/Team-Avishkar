"""
ChandraMatch Streaming Dataset Pipeline (Module B2 + B4 Infrastructure)

Streams bounded tiles from remote PDS4 Chandrayaan-2 products, executes B4 baseline
preprocessing, preserves metadata/mask provenance, and generates deterministic datasets.
"""
import os
import json
import time
import urllib.request
from typing import Dict, Any, List, Optional
import numpy as np

# Import B2 and B4 without modifying them
from pipeline.loader import read_remote_window, read_remote_metadata
from pipeline.preprocessor import preprocess_image


def get_final_url(initial_url: str) -> str:
    """Resolve HTTP redirects to direct LFS/CDN storage URL."""
    req = urllib.request.Request(initial_url, method='HEAD')
    with urllib.request.urlopen(req) as resp:
        return resp.geturl()


class StreamingDatasetPipeline:
    """
    Production-ready remote streaming dataset pipeline.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.tiles_dir = os.path.join(output_dir, "tiles")
        self.manifest_path = os.path.join(output_dir, "dataset_manifest.json")
        
        os.makedirs(self.tiles_dir, exist_ok=True)
        self._init_manifest()

    def _init_manifest(self):
        if not os.path.exists(self.manifest_path):
            manifest_data = {
                "dataset_name": "Chandrayaan2_Remote_Streaming_Dataset",
                "creation_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_tiles": 0,
                "tiles": {}
            }
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)

    def load_manifest(self) -> Dict[str, Any]:
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_manifest(self, manifest_data: Dict[str, Any]):
        tmp_path = self.manifest_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        os.replace(tmp_path, self.manifest_path)

    def is_tile_processed(self, tile_id: str) -> bool:
        manifest = self.load_manifest()
        if tile_id in manifest["tiles"]:
            tile_file = os.path.join(self.tiles_dir, f"{tile_id}.npz")
            return os.path.exists(tile_file)
        return False

    def process_tile(
        self,
        product_id: str,
        sensor: str,
        img_url: str,
        xml_metadata: Dict[str, Any],
        row_start: int,
        row_end: int,
        col_start: int,
        col_end: int,
        dataset_split: str = "train"
    ) -> Dict[str, Any]:
        """
        Process a single bounded tile from a remote product.
        """
        # Deterministic tile naming
        tile_id = f"{product_id}__r{row_start}_{row_end}__c{col_start}_{col_end}"
        
        # Check if already processed (resumability)
        if self.is_tile_processed(tile_id):
            manifest = self.load_manifest()
            return manifest["tiles"][tile_id]

        # 1. Fetch remote bounded window via B2
        resolved_img_url = get_final_url(img_url)
        raw_dtype_str = "uint8" if sensor == "OHRC" else ">u2"
        raw_dtype = np.dtype(raw_dtype_str)
        
        byte_offset = xml_metadata.get("byte_offset", 0)
        full_width = xml_metadata["width"]
        full_height = xml_metadata["height"]
        
        raw_window = read_remote_window(
            img_url=resolved_img_url,
            width=full_width,
            height=full_height,
            dtype=raw_dtype,
            row_start=row_start,
            row_end=row_end,
            col_start=col_start,
            col_end=col_end,
            byte_offset=byte_offset
        )

        # 2. Preprocess tile via B4 (baseline default settings)
        tile_input = {
            "array": raw_window,
            "width": col_end - col_start,
            "height": row_end - row_start
        }
        b4_out = preprocess_image(tile_input, working_scale=1.0, apply_clahe=False)

        # 3. Calculate provenance & metadata
        valid_count = int(np.count_nonzero(b4_out["mask"] > 0))
        total_count = int(b4_out["mask"].size)
        valid_fraction = float(valid_count / total_count) if total_count > 0 else 0.0

        gsd = float(xml_metadata.get("resolution_m", 0.25 if sensor == "OHRC" else 4.48))
        phys_w = float((col_end - col_start) * gsd)
        phys_h = float((row_end - row_start) * gsd)

        tile_record = {
            "tile_id": tile_id,
            "product_id": product_id,
            "sensor": sensor,
            "dataset_split": dataset_split,
            "source_url": img_url,
            "source_row_start": row_start,
            "source_row_end": row_end,
            "source_col_start": col_start,
            "source_col_end": col_end,
            "tile_width": col_end - col_start,
            "tile_height": row_end - row_start,
            "native_full_width": full_width,
            "native_full_height": full_height,
            "native_dtype": str(raw_dtype),
            "preprocessed_dtype": "uint8",
            "gsd_m_per_pixel": gsd,
            "physical_width_m": phys_w,
            "physical_height_m": phys_h,
            "valid_fraction": valid_fraction,
            "raw_min": int(raw_window.min()),
            "raw_max": int(raw_window.max()),
            "raw_mean": float(raw_window.mean()),
            "prep_min": int(b4_out["image"].min()),
            "prep_max": int(b4_out["image"].max()),
            "prep_mean": float(b4_out["image"].mean()),
            "preprocessing_version": "B4_v1.0_baseline",
            "created_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rel_filepath": f"tiles/{tile_id}.npz"
        }

        # 4. Atomic file save (NPZ format containing raw, preprocessed, and mask arrays)
        save_path = os.path.join(self.tiles_dir, f"{tile_id}.npz")
        tmp_save_path = os.path.join(self.tiles_dir, f"{tile_id}_tmp.npz")
        with open(tmp_save_path, "wb") as f:
            np.savez_compressed(
                f,
                raw=raw_window,
                preprocessed=b4_out["image"],
                mask=b4_out["mask"]
            )
        os.replace(tmp_save_path, save_path)

        # 5. Update Manifest
        manifest = self.load_manifest()
        manifest["tiles"][tile_id] = tile_record
        manifest["total_tiles"] = len(manifest["tiles"])
        self.save_manifest(manifest)

        return tile_record
