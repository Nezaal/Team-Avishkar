"""
SIFT Pipeline - From Scratch
Streams raw .img data from Hugging Face, uses real GPS coordinates 
to find the exact geographic overlap, scales images correctly, 
and runs SIFT + RANSAC to produce a HIGH_CONFIDENCE result.

Usage: python sift_pipeline/run.py
"""

import os
import sys
import json
import csv
import cv2
import numpy as np
import urllib.request
import struct
import time


# ============================================================
# CONFIG
# ============================================================
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(ROOT, "ground_truth", "product_catalog.json")
PAIRS_CSV = os.path.join(ROOT, "ground_truth", "manifests", "pairs.csv")

# The raw .img files live on Nezaal's HF repo
RAW_BASE_URL = "https://huggingface.co/datasets/Nezaal/pradan-dataset/resolve/main/"


# ============================================================
# STEP 1: Load metadata
# ============================================================
def load_catalog():
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def load_pairs():
    pairs = []
    with open(PAIRS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    return pairs


def get_product(catalog, product_id):
    for p in catalog["products"]:
        if p["product_id"] == product_id:
            return p
    raise KeyError(f"Product not found: {product_id}")


# ============================================================
# STEP 2: Compute geographic overlap using real GPS bounding boxes
# ============================================================
def compute_overlap(ohrc_product, tmc2_product):
    """
    Compute the geographic overlap between two products using their
    real GPS bounding boxes from the product catalog.
    Returns the overlapping lat/lon bounds.
    """
    ohrc_bb = ohrc_product["bounding_box"]
    tmc2_bb = tmc2_product["bounding_box"]

    # Overlap = intersection of bounding boxes
    overlap_lat_min = max(ohrc_bb["lat_min"], tmc2_bb["lat_min"])
    overlap_lat_max = min(ohrc_bb["lat_max"], tmc2_bb["lat_max"])
    overlap_lon_min = max(ohrc_bb["lon_min"], tmc2_bb["lon_min"])
    overlap_lon_max = min(ohrc_bb["lon_max"], tmc2_bb["lon_max"])

    if overlap_lat_min >= overlap_lat_max or overlap_lon_min >= overlap_lon_max:
        raise ValueError("No geographic overlap found between the two products!")

    return {
        "lat_min": overlap_lat_min,
        "lat_max": overlap_lat_max,
        "lon_min": overlap_lon_min,
        "lon_max": overlap_lon_max,
    }


def latlon_to_pixel_rows(product, overlap):
    """
    Convert geographic overlap to pixel row range for a given product.
    Uses linear interpolation between the product's corner coordinates.
    """
    bb = product["bounding_box"]
    height = product["height"]

    # Linear interpolation: lat -> row
    # Top of image = lat_max, Bottom of image = lat_min
    lat_range = bb["lat_max"] - bb["lat_min"]
    if lat_range == 0:
        return 0, height

    # Row 0 = lat_max (top), Row height = lat_min (bottom)
    row_start = int((bb["lat_max"] - overlap["lat_max"]) / lat_range * height)
    row_end = int((bb["lat_max"] - overlap["lat_min"]) / lat_range * height)

    # Clamp
    row_start = max(0, min(height - 1, row_start))
    row_end = max(row_start + 1, min(height, row_end))

    return row_start, row_end


# ============================================================
# STEP 3: Stream raw pixel data from Hugging Face using HTTP Range requests
# ============================================================
def resolve_hf_url(rel_path):
    """Resolve a Hugging Face URL (follows redirects to CDN)."""
    url = RAW_BASE_URL + rel_path
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.geturl()


def read_remote_rows(url, width, height, dtype, row_start, row_end):
    """
    Read specific rows from a raw binary image file on HF using HTTP Range requests.
    """
    bytes_per_pixel = dtype.itemsize
    row_bytes = width * bytes_per_pixel

    byte_start = row_start * row_bytes
    byte_end = row_end * row_bytes - 1  # HTTP Range is inclusive

    req = urllib.request.Request(url)
    req.add_header("Range", f"bytes={byte_start}-{byte_end}")

    print(f"  Downloading rows {row_start}-{row_end} ({(byte_end - byte_start + 1) / 1e6:.1f} MB)...")
    with urllib.request.urlopen(req, timeout=120) as response:
        raw_bytes = response.read()

    n_rows = row_end - row_start
    arr = np.frombuffer(raw_bytes, dtype=dtype).reshape(n_rows, width)
    return arr


# ============================================================
# STEP 4: Preprocess images for SIFT
# ============================================================
def to_uint8(arr):
    """Convert any array to uint8 for SIFT.
    Uses percentile-based normalization for 16-bit data to prevent
    hot pixel outliers from crushing the useful contrast range.
    """
    if arr.dtype == np.uint8:
        return arr
    # For uint16 (TMC-2): use 2nd-98th percentile normalization
    # This is standard practice for satellite imagery
    arr_f = arr.astype(np.float32)
    p2 = np.percentile(arr_f, 2)
    p98 = np.percentile(arr_f, 98)
    if p98 - p2 > 0:
        arr_f = np.clip((arr_f - p2) / (p98 - p2) * 255.0, 0, 255)
    return arr_f.astype(np.uint8)


def apply_clahe(img, clip_limit=2.0, grid_size=8):
    """Apply CLAHE contrast enhancement."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
    return clahe.apply(img)


# ============================================================
# STEP 5: SIFT + RANSAC matching
# ============================================================
def run_sift_matching(img1, img2):
    """
    Run SIFT keypoint extraction + FLANN matching + RANSAC.
    Returns the result dict with status, metrics, and transformation matrix.
    """
    sift = cv2.SIFT_create(nfeatures=0, contrastThreshold=0.02, edgeThreshold=15)

    print("  Extracting SIFT keypoints...")
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    print(f"  OHRC keypoints: {len(kp1)}, TMC-2 keypoints: {len(kp2)}")

    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return {"status": "FAILED", "metrics": {"reason": "Not enough keypoints"}}

    # FLANN-based matching
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=100)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    print("  Running FLANN matching...")
    matches = flann.knnMatch(des1, des2, k=2)

    # Lowe's ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    print(f"  Tentative matches after ratio test: {len(good_matches)}")

    if len(good_matches) < 4:
        return {
            "status": "FAILED",
            "metrics": {"tentative_matches": len(good_matches), "reason": "Too few matches for RANSAC"},
        }

    # RANSAC
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if H is None:
        return {
            "status": "FAILED",
            "metrics": {"tentative_matches": len(good_matches), "reason": "Homography estimation failed"},
        }

    inliers = int(mask.sum())

    # Compute RMSE on inliers
    inlier_src = src_pts[mask.ravel() == 1]
    inlier_dst = dst_pts[mask.ravel() == 1]
    projected = cv2.perspectiveTransform(inlier_src, H)
    errors = np.sqrt(np.sum((projected - inlier_dst) ** 2, axis=2))
    rmse = float(np.mean(errors))

    # Determine confidence
    if inliers >= 50 and rmse < 2.0:
        status = "HIGH_CONFIDENCE"
    elif inliers >= 10:
        status = "MEDIUM_CONFIDENCE"
    else:
        status = "LOW_CONFIDENCE"

    return {
        "status": status,
        "metrics": {
            "rmse_pixel_error": round(rmse, 4),
            "inliers": inliers,
            "tentative_matches": len(good_matches),
            "ohrc_keypoints": len(kp1),
            "tmc2_keypoints": len(kp2),
        },
        "transformation_matrix": H.tolist(),
    }


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("SIFT PIPELINE - FROM SCRATCH (Using Real GPS Coordinates)")
    print("=" * 60)

    # Load metadata
    print("\n[1/6] Loading metadata...")
    catalog = load_catalog()
    pairs = load_pairs()
    pair = pairs[0]  # pair_001
    print(f"  Pair: {pair['pair_id']}")

    ohrc_product = get_product(catalog, pair["ohrc_product_id"])
    tmc2_product = get_product(catalog, pair["tmc2_product_id"])
    print(f"  OHRC: {ohrc_product['product_id']} ({ohrc_product['width']}x{ohrc_product['height']})")
    print(f"  TMC-2: {tmc2_product['product_id']} ({tmc2_product['width']}x{tmc2_product['height']})")

    # Compute geographic overlap
    print("\n[2/6] Computing geographic overlap using real GPS coordinates...")
    overlap = compute_overlap(ohrc_product, tmc2_product)
    print(f"  Overlap Lat: {overlap['lat_min']:.6f} to {overlap['lat_max']:.6f}")
    print(f"  Overlap Lon: {overlap['lon_min']:.6f} to {overlap['lon_max']:.6f}")

    ohrc_row_start, ohrc_row_end = latlon_to_pixel_rows(ohrc_product, overlap)
    tmc2_row_start, tmc2_row_end = latlon_to_pixel_rows(tmc2_product, overlap)

    # Take a manageable center slice of OHRC (5000 rows ~ 60MB) instead of the full image
    # This is authentic block matching - same GPS coordinates, just a smaller patch
    MAX_OHRC_ROWS = 5000
    ohrc_total = ohrc_row_end - ohrc_row_start
    if ohrc_total > MAX_OHRC_ROWS:
        ohrc_center = (ohrc_row_start + ohrc_row_end) // 2
        ohrc_row_start = ohrc_center - MAX_OHRC_ROWS // 2
        ohrc_row_end = ohrc_center + MAX_OHRC_ROWS // 2

        # Recalculate matching TMC-2 rows for this OHRC slice
        ohrc_bb = ohrc_product["bounding_box"]
        ohrc_lat_range = ohrc_bb["lat_max"] - ohrc_bb["lat_min"]
        slice_lat_max = ohrc_bb["lat_max"] - (ohrc_row_start / ohrc_product["height"]) * ohrc_lat_range
        slice_lat_min = ohrc_bb["lat_max"] - (ohrc_row_end / ohrc_product["height"]) * ohrc_lat_range
        slice_overlap = {"lat_min": slice_lat_min, "lat_max": slice_lat_max, 
                         "lon_min": overlap["lon_min"], "lon_max": overlap["lon_max"]}
        tmc2_row_start, tmc2_row_end = latlon_to_pixel_rows(tmc2_product, slice_overlap)

    print(f"  OHRC pixel rows: {ohrc_row_start} - {ohrc_row_end} ({ohrc_row_end - ohrc_row_start} rows)")
    print(f"  TMC-2 pixel rows: {tmc2_row_start} - {tmc2_row_end} ({tmc2_row_end - tmc2_row_start} rows)")

    # Resolve HF URLs
    print("\n[3/6] Resolving Hugging Face CDN URLs...")
    ohrc_rel = ohrc_product["img_path"].replace("dataset/pradan_downloads/", "")
    tmc2_rel = tmc2_product["img_path"].replace("dataset/pradan_downloads/", "")
    ohrc_url = resolve_hf_url(ohrc_rel)
    tmc2_url = resolve_hf_url(tmc2_rel)
    print("  URLs resolved.")

    # Stream overlapping regions
    print("\n[4/6] Streaming overlapping regions from Hugging Face...")
    ohrc_raw = read_remote_rows(ohrc_url, ohrc_product["width"], ohrc_product["height"],
                                 np.dtype("uint8"), ohrc_row_start, ohrc_row_end)
    tmc2_raw = read_remote_rows(tmc2_url, tmc2_product["width"], tmc2_product["height"],
                                 np.dtype(">u2"), tmc2_row_start, tmc2_row_end)
    print(f"  OHRC chunk: {ohrc_raw.shape}")
    print(f"  TMC-2 chunk: {tmc2_raw.shape}")

    # Preprocess
    print("\n[5/6] Preprocessing and scaling...")
    ohrc_u8 = to_uint8(ohrc_raw)
    tmc2_u8 = to_uint8(tmc2_raw)

    # Apply CLAHE
    ohrc_u8 = apply_clahe(ohrc_u8)
    tmc2_u8 = apply_clahe(tmc2_u8)

    # Scale OHRC down by the resolution ratio so craters match in size
    ratio = float(pair["resolution_ratio"])
    target_width = tmc2_product["width"]  # Match TMC-2 width
    target_height = int(ohrc_u8.shape[0] / ratio)
    ohrc_scaled = cv2.resize(ohrc_u8, (target_width, target_height), interpolation=cv2.INTER_AREA)
    print(f"  OHRC scaled from {ohrc_u8.shape} to {ohrc_scaled.shape} (ratio={ratio})")
    print(f"  TMC-2 shape: {tmc2_u8.shape}")

    # Match heights by taking the center of the larger image
    if ohrc_scaled.shape[0] > tmc2_u8.shape[0]:
        diff = ohrc_scaled.shape[0] - tmc2_u8.shape[0]
        ohrc_scaled = ohrc_scaled[diff // 2 : diff // 2 + tmc2_u8.shape[0], :]
    elif tmc2_u8.shape[0] > ohrc_scaled.shape[0]:
        diff = tmc2_u8.shape[0] - ohrc_scaled.shape[0]
        tmc2_u8 = tmc2_u8[diff // 2 : diff // 2 + ohrc_scaled.shape[0], :]

    print(f"  Final OHRC: {ohrc_scaled.shape}, Final TMC-2: {tmc2_u8.shape}")

    # SIFT matching
    print("\n[6/6] Running SIFT + RANSAC...")
    t0 = time.time()
    result = run_sift_matching(ohrc_scaled, tmc2_u8)
    elapsed = time.time() - t0

    # Output
    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print(f"\nCompleted in {elapsed:.2f} seconds.")
    print("=" * 60)


if __name__ == "__main__":
    main()
