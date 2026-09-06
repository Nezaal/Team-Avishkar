"""
Safe smoke test for the ChandraMatch preprocessing pipeline.

Loads only a small crop from the center of each image (via memmap)
instead of the full ~1-2 GB images. Uses < 50 MB RAM.

Usage:
    python backend/pipeline/_test_runner.py [pair_id]
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from pipeline.loader import ImageLoader
from pipeline.pair_analyzer import PairAnalyzer, compute_contrast, recommend_working_scale
from pipeline.preprocessor import preprocess_image
from pipeline.runner import get_pair


CROP_SIZE = 1500  # pixels, both dimensions


def crawl_center(image_dict, crop_size=CROP_SIZE):
    """
    Slice a small crop from the center of a memmapped image.
    Uses memmap slicing - only those few pages get read from disk.
    Returns a normal numpy array (small, copied).
    """
    arr = image_dict["array"]
    h, w = arr.shape[:2]
    crop = min(crop_size, h, w)
    cy, cx = h // 2, w // 2
    y0, y1 = cy - crop // 2, cy + crop // 2
    x0, x1 = cx - crop // 2, cx + crop // 2
    return np.array(arr[y0:y1, x0:x1], copy=True)


def make_crop_dict(image_dict, crop_array):
    """Wrap a crop array into the image_data dict format expected by preprocess_image."""
    return {
        "array": crop_array,
        "width": crop_array.shape[1],
        "height": crop_array.shape[0],
        "channels": 1,
        "dtype": str(crop_array.dtype),
        "metadata": image_dict["metadata"],
    }


def main():
    pair_id = sys.argv[1] if len(sys.argv) > 1 else "pair_001"
    pair = get_pair(pair_id)

    print("=" * 62)
    print(f"SAFE SMOKE TEST - {pair_id} (crops only, no full-image loads)")
    print("=" * 62)
    print(f"  OHRC : {pair['ohrc_product_id']}")
    print(f"  TMC-2: {pair['tmc2_product_id']}")
    print(f"  Full dims: OHRC {pair['ohrc_width']}x{pair['ohrc_height']} | "
          f"TMC-2 {pair['tmc2_width']}x{pair['tmc2_height']}")

    loader = ImageLoader()

    # --- Stage 1: Loader ---
    print("\n[1/4] Loader (memmap)...")
    ohrc = loader.load(pair["ohrc_product_id"])
    tmc2 = loader.load(pair["tmc2_product_id"])
    assert type(ohrc["array"]) is np.memmap, "loader should return memmap"
    assert ohrc["width"] == int(pair["ohrc_width"]) and ohrc["height"] == int(pair["ohrc_height"])
    print(f"  Loaded memmaps: OHRC {ohrc['array'].shape} {ohrc['dtype']} | "
          f"TMC-2 {tmc2['array'].shape} {tmc2['dtype']}")
    print(f"  Metadata: sensor={ohrc['metadata']['sensor']}, "
          f"res={ohrc['metadata']['pixel_resolution_m']} m/px")

    ohrc_crop = crawl_center(ohrc)
    tmc2_crop = crawl_center(tmc2)
    print(f"  Crops: OHRC {ohrc_crop.shape} {ohrc_crop.dtype} | "
          f"TMC-2 {tmc2_crop.shape} {tmc2_crop.dtype}")
    print(f"  Crop ranges: OHRC [{ohrc_crop.min()},{ohrc_crop.max()}] | "
          f"TMC-2 [{tmc2_crop.min()},{tmc2_crop.max()}]")

    ohrc_dict = make_crop_dict(ohrc, ohrc_crop)
    tmc2_dict = make_crop_dict(tmc2, tmc2_crop)

    # --- Stage 2: Analyzer ---
    print("\n[2/4] Pair Analyzer...")
    analyzer = PairAnalyzer()
    analysis = analyzer.analyze(ohrc_dict, tmc2_dict)
    analyzer.print_report(analysis)

    # --- Stage 3: Preprocessor ---
    print("\n[3/4] Preprocessor...")
    src_scale = analysis["source_working_scale"]
    ref_scale = analysis["reference_working_scale"]
    clahe = analysis["recommend_clahe"]

    src_pre = preprocess_image(ohrc_dict, working_scale=src_scale, clahe_clip=2.0, apply_clahe=clahe)
    ref_pre = preprocess_image(tmc2_dict, working_scale=ref_scale, clahe_clip=2.0, apply_clahe=False)

    print(f"  Source ops: {src_pre['operations']}")
    print(f"  Reference ops: {ref_pre['operations']}")
    print(f"  Source output: {src_pre['working_width']}x{src_pre['working_height']} "
          f"uint8 range=[{src_pre['image'].min()},{src_pre['image'].max()}]")
    print(f"  Reference output: {ref_pre['working_width']}x{ref_pre['working_height']} "
          f"uint8 range=[{ref_pre['image'].min()},{ref_pre['image'].max()}]")

    # --- Stage 4: Save PNG previews ---
    print("\n[4/4] Saving preview PNGs...")
    out_dir = os.path.join(os.path.dirname(__file__), "_preview")
    os.makedirs(out_dir, exist_ok=True)
    src_path = os.path.join(out_dir, f"{pair_id}_ohrc.png")
    ref_path = os.path.join(out_dir, f"{pair_id}_tmc2.png")
    try:
        import cv2
        cv2.imwrite(src_path, src_pre["image"])
        cv2.imwrite(ref_path, ref_pre["image"])
    except ImportError:
        from PIL import Image
        Image.fromarray(src_pre["image"]).save(src_path)
        Image.fromarray(ref_pre["image"]).save(ref_path)
    print(f"  Saved: {src_path}")
    print(f"  Saved: {ref_path}")

    print("\n" + "=" * 62)
    print("SAFE SMOKE TEST PASSED - all stages work on crops")
    print("=" * 62)


if __name__ == "__main__":
    main()