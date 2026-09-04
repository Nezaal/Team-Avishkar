"""
Find overlapping OHRC and TMC-2 pairs from the product catalog.

Uses a proximity-based approach: checks if TMC-2 geometry points are
near the OHRC bounding box (within a configurable tolerance), since
TMC-2 strips are narrow orbital tracks and the 100-pixel sampling
may not place points exactly inside the OHRC bbox.

Usage:
    python ground_truth/sources/find_pairs.py
"""
import csv
import json
import math
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOG_FILE = os.path.join(ROOT, "ground_truth", "product_catalog.json")
OUTPUT_FILE = os.path.join(ROOT, "ground_truth", "manifests", "pairs.csv")

# Proximity tolerance in degrees. TMC-2 strips are ~20km wide (~0.2 deg at equator,
# ~0.4 deg at poles). The 100-pixel sampling interval is ~0.09 deg.
# Using 1.5 deg tolerance catches strips that pass through the OHRC region
# even if the sampled points don't land exactly inside the bbox.
PROXIMITY_TOL_DEG = 1.5

# Minimum points required within proximity zone
MIN_POINTS_NEAR = 5


def normalize_longitude(lon):
    return ((lon + 180) % 360) - 180


def describe_region(lat_min, lat_max, lon_min, lon_max):
    mean_lat = (lat_min + lat_max) / 2
    mean_lon = (lon_min + lon_max) / 2
    if mean_lat < -65:
        lat_desc = "South_Polar"
    elif mean_lat < -30:
        lat_desc = "Southern"
    elif mean_lat < -10:
        lat_desc = "Mid_South"
    elif mean_lat < 10:
        lat_desc = "Equatorial"
    else:
        lat_desc = "Northern"
    lon_dir = "E" if mean_lon >= 0 else "W"
    return f"{lat_desc}_{abs(mean_lon):.0f}{lon_dir}"


def find_tmc2_near_ohrc(df, ohrc_bbox, tol):
    """
    Vectorized check: find TMC-2 geometry points near the OHRC bounding box.
    Returns (points_inside, points_near, fraction_near).
    """
    lon_norm = ((df["Longitude"].values + 180) % 360) - 180
    lat = df["Latitude"].values
    total = len(df)

    # Exact inside check
    in_lat = (lat >= ohrc_bbox["lat_min"]) & (lat <= ohrc_bbox["lat_max"])
    if ohrc_bbox["lon_min"] <= ohrc_bbox["lon_max"]:
        in_lon = (lon_norm >= ohrc_bbox["lon_min"]) & (lon_norm <= ohrc_bbox["lon_max"])
    else:
        in_lon = (lon_norm >= ohrc_bbox["lon_min"]) | (lon_norm <= ohrc_bbox["lon_max"])
    inside = in_lat & in_lon

    # Proximity check (expanded bbox)
    in_lat_near = (lat >= ohrc_bbox["lat_min"] - tol) & (lat <= ohrc_bbox["lat_max"] + tol)
    if ohrc_bbox["lon_min"] <= ohrc_bbox["lon_max"]:
        in_lon_near = (lon_norm >= ohrc_bbox["lon_min"] - tol) & (lon_norm <= ohrc_bbox["lon_max"] + tol)
    else:
        in_lon_near = (lon_norm >= ohrc_bbox["lon_min"] - tol) | (lon_norm <= ohrc_bbox["lon_max"] + tol)
    near = in_lat_near & in_lon_near

    n_inside = int(np.sum(inside))
    n_near = int(np.sum(near))
    return n_inside, n_near, n_near / total if total > 0 else 0.0


def main():
    print("=" * 60)
    print("Finding overlapping OHRC and TMC-2 pairs")
    print(f"Proximity tolerance: {PROXIMITY_TOL_DEG} deg")
    print("=" * 60)

    with open(CATALOG_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    ohrc_products = [p for p in catalog["products"] if p["sensor"] == "OHRC"]
    tmc2_products = [p for p in catalog["products"] if p["sensor"] == "TMC-2"]

    print(f"\nOHRC products: {len(ohrc_products)}")
    print(f"TMC-2 products: {len(tmc2_products)}")

    # Pre-load all TMC-2 geometry CSVs
    print("\nLoading TMC-2 geometry CSVs...")
    tmc2_geoms = {}
    for tmc2 in tmc2_products:
        csv_path = tmc2.get("geometry_csv")
        if csv_path:
            full_path = os.path.join(ROOT, csv_path)
            if os.path.exists(full_path):
                try:
                    df = pd.read_csv(full_path)
                    tmc2_geoms[tmc2["product_id"]] = df
                except Exception as e:
                    print(f"  [ERROR] {tmc2['product_id'][:50]}: {e}")
    print(f"Loaded {len(tmc2_geoms)} TMC-2 geometry CSVs")

    # Find overlapping pairs
    print("\nChecking spatial overlap...")
    pairs = []

    for ohrc in ohrc_products:
        if not ohrc.get("bounding_box"):
            continue

        ohrc_bb = ohrc["bounding_box"]
        matches = []

        for tmc2 in tmc2_products:
            tmc2_id = tmc2["product_id"]
            if tmc2_id not in tmc2_geoms:
                continue

            df = tmc2_geoms[tmc2_id]
            n_inside, n_near, fraction = find_tmc2_near_ohrc(df, ohrc_bb, PROXIMITY_TOL_DEG)

            if n_near >= MIN_POINTS_NEAR:
                resolution_ratio = tmc2["pixel_resolution_m"] / ohrc["pixel_resolution_m"]
                matches.append({
                    "tmc2": tmc2,
                    "points_inside": n_inside,
                    "points_near": n_near,
                    "fraction": fraction,
                    "resolution_ratio": resolution_ratio,
                })

        if matches:
            matches.sort(key=lambda m: m["points_near"], reverse=True)
            for m in matches:
                tmc2 = m["tmc2"]
                region = describe_region(
                    ohrc_bb["lat_min"], ohrc_bb["lat_max"],
                    ohrc_bb["lon_min"], ohrc_bb["lon_max"],
                )
                pairs.append({
                    "ohrc_product_id": ohrc["product_id"],
                    "tmc2_product_id": tmc2["product_id"],
                    "ohrc_img_path": ohrc["img_path"],
                    "tmc2_img_path": tmc2["img_path"],
                    "ohrc_geometry_csv": ohrc.get("geometry_csv", ""),
                    "tmc2_geometry_csv": tmc2.get("geometry_csv", ""),
                    "ohrc_width": ohrc["width"],
                    "ohrc_height": ohrc["height"],
                    "tmc2_width": tmc2["width"],
                    "tmc2_height": tmc2["height"],
                    "ohrc_dtype": ohrc["dtype"],
                    "tmc2_dtype": tmc2["dtype"],
                    "ohrc_resolution_m": ohrc["pixel_resolution_m"],
                    "tmc2_resolution_m": tmc2["pixel_resolution_m"],
                    "resolution_ratio": round(m["resolution_ratio"], 2),
                    "tmc2_points_inside": m["points_inside"],
                    "tmc2_points_near": m["points_near"],
                    "overlap_fraction": round(m["fraction"], 6),
                    "region": region,
                })
            inside_info = [f"{m['points_inside']}in/{m['points_near']}near" for m in matches]
            print(f"  {ohrc['product_id'][:50]}: {len(matches)} matches ({', '.join(inside_info[:3])})")
        else:
            print(f"  {ohrc['product_id'][:50]}: NO matches")

    # Sort by points_near descending (best overlap first)
    pairs.sort(key=lambda p: p["tmc2_points_near"], reverse=True)

    # Assign pair IDs
    for i, p in enumerate(pairs):
        p["pair_id"] = f"pair_{i + 1:03d}"

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    if pairs:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=pairs[0].keys())
            writer.writeheader()
            writer.writerows(pairs)

    print(f"\n{'=' * 60}")
    print(f"Pairs found: {len(pairs)}")
    print(f"Written to: {OUTPUT_FILE}")
    print(f"{'=' * 60}")

    if pairs:
        print(f"\nTop pairs by proximity:")
        for p in pairs[:15]:
            print(
                f"  {p['pair_id']}: "
                f"{p['ohrc_product_id'][:42]} "
                f"vs {p['tmc2_product_id'][:42]} "
                f"({p['tmc2_points_inside']}in/{p['tmc2_points_near']}near, "
                f"ratio={p['resolution_ratio']:.1f}x, "
                f"{p['region']})"
            )

    tmc2_used = set(p["tmc2_product_id"] for p in pairs)
    ohrc_used = set(p["ohrc_product_id"] for p in pairs)
    print(f"\nUnique OHRC scenes paired: {len(ohrc_used)}/{len(ohrc_products)}")
    print(f"Unique TMC-2 strips used: {len(tmc2_used)}/{len(tmc2_products)}")


if __name__ == "__main__":
    main()
