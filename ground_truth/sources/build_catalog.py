"""
Build product_catalog.json from downloaded OHRC and TMC-2 products.

Scans dataset/pradan_downloads/{ohrc,tmc-2}/, reads each product's PDS4 XML
metadata and geometry CSV, and produces a machine-readable catalog with
image dimensions, data types, pixel resolution, geographic bounding boxes,
and file paths.

Usage:
    python ground_truth/sources/build_catalog.py
"""
import glob
import json
import os
import xml.etree.ElementTree as ET

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOWNLOAD_DIR = os.path.join(ROOT, "dataset", "pradan_downloads")
OUTPUT_FILE = os.path.join(ROOT, "ground_truth", "product_catalog.json")

# PDS4 namespaces used in Chandrayaan-2 XML labels
NS = {
    "pds": "http://pds.nasa.gov/pds4/pds/v1",
    "isda": "https://isda.issdc.gov.in/pds4/isda/v1",
}

# Mapping from PDS4 data_type strings to numpy dtype
DTYPE_MAP = {
    "UnsignedByte": "uint8",
    "UnsignedLSB2": "uint16",
    "UnsignedMSB2": "uint16",
    "SignedLSB2": "int16",
    "SignedMSB2": "int16",
    "UnsignedLSB4": "uint32",
    "UnsignedMSB4": "uint32",
    "SignedLSB4": "int32",
    "SignedMSB4": "int32",
    "IEEE754LSBSingle": "float32",
    "IEEE754MSBSingle": "float32",
}


def normalize_longitude(lon):
    return ((lon + 180) % 360) - 180


def parse_xml_metadata(xml_path):
    """Extract image dimensions, data type, resolution, corners from PDS4 XML."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Image dimensions from Array_2D_Image/Axis_Array
    # Children are in pds namespace: axis_name, elements, sequence_number
    axis_arrays = root.findall(".//pds:Array_2D_Image/pds:Axis_Array", NS)

    height = None
    width = None
    for axis in axis_arrays:
        axis_name = axis.find("pds:axis_name", NS)
        elements = axis.find("pds:elements", NS)
        if axis_name is not None and elements is not None:
            name = axis_name.text
            count = int(elements.text)
            if name == "Line":
                height = count
            elif name == "Sample":
                width = count

    # Data type
    data_type_elem = root.find(".//pds:Element_Array/pds:data_type", NS)
    data_type_str = data_type_elem.text if data_type_elem is not None else None
    numpy_dtype = DTYPE_MAP.get(data_type_str, data_type_str)

    # Pixel resolution
    pix_res_elem = root.find(".//isda:pixel_resolution", NS)
    pixel_resolution = None
    if pix_res_elem is not None:
        pixel_resolution = float(pix_res_elem.text)

    # File size
    file_size_elem = root.find(".//pds:File/pds:file_size", NS)
    file_size = int(file_size_elem.text) if file_size_elem is not None else None

    # Refined corner coordinates
    corners = {}
    refined = root.find(".//isda:Refined_Corner_Coordinates", NS)
    if refined is None:
        refined = root.find(".//isda:Refined_Corner_Coordinates")
    if refined is not None:
        for prefix in ["upper_left", "upper_right", "lower_left", "lower_right"]:
            lat_elem = refined.find(f"isda:{prefix}_latitude", NS)
            lon_elem = refined.find(f"isda:{prefix}_longitude", NS)
            if lat_elem is None:
                lat_elem = refined.find(f"{prefix}_latitude")
            if lon_elem is None:
                lon_elem = refined.find(f"{prefix}_longitude")
            if lat_elem is not None and lon_elem is not None:
                corners[f"{prefix}_lat"] = float(lat_elem.text)
                corners[f"{prefix}_lon"] = normalize_longitude(float(lon_elem.text))

    # Projection and area
    projection_elem = root.find(".//isda:projection", NS)
    area_elem = root.find(".//isda:area", NS)
    projection = projection_elem.text if projection_elem is not None else None
    area = area_elem.text if area_elem is not None else None

    # Instrument name
    instrument_elem = root.find(
        ".//Observing_System/Observing_System_Component/instrument_name", NS
    )
    if instrument_elem is None:
        instrument_elem = root.find(
            ".//Observing_System/Observing_System_Component/instrument_name"
        )
    instrument = instrument_elem.text if instrument_elem is not None else None

    return {
        "width": width,
        "height": height,
        "data_type_pds4": data_type_str,
        "dtype": numpy_dtype,
        "pixel_resolution_m": pixel_resolution,
        "file_size_bytes": file_size,
        "corners": corners,
        "projection": projection,
        "area": area,
        "instrument": instrument,
    }


def compute_bounding_box_from_csv(csv_path):
    """Read geometry CSV and compute geographic bounding box."""
    df = pd.read_csv(csv_path)
    df["Longitude_norm"] = normalize_longitude(df["Longitude"])
    return {
        "lat_min": float(df["Latitude"].min()),
        "lat_max": float(df["Latitude"].max()),
        "lon_min": float(df["Longitude_norm"].min()),
        "lon_max": float(df["Longitude_norm"].max()),
    }


def discover_products(sensor_dir, sensor_name):
    """Find all products under a sensor download directory."""
    products = []
    xml_pattern = os.path.join(sensor_dir, "*", "data", "calibrated", "*", "*.xml")
    xml_files = sorted(glob.glob(xml_pattern))

    for xml_path in xml_files:
        # Derive product_id from directory structure:
        # sensor_dir/<product_id>/data/calibrated/<date>/<product>.xml
        # So product_id is 3 parents up from the xml file's parent dir
        product_dir = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(xml_path))))
        )
        # Find corresponding .img file
        img_path = xml_path.replace(".xml", ".img")
        if not os.path.exists(img_path):
            print(f"  [SKIP] No .img file for {product_dir}")
            continue

        # Find geometry CSV under the product directory
        geo_pattern = os.path.join(
            sensor_dir, product_dir, "geometry", "calibrated", "*", "*.csv"
        )
        geo_matches = sorted(glob.glob(geo_pattern))
        geo_csv = geo_matches[0] if geo_matches else None

        # Parse XML metadata
        try:
            meta = parse_xml_metadata(xml_path)
        except Exception as e:
            print(f"  [ERROR] Parsing XML for {product_dir}: {e}")
            continue

        # Compute bounding box from geometry CSV
        bbox = None
        if geo_csv and os.path.exists(geo_csv):
            try:
                bbox = compute_bounding_box_from_csv(geo_csv)
            except Exception as e:
                print(f"  [WARN] CSV bbox failed for {product_dir}: {e}")

        # If no CSV bbox, derive from XML corners
        if bbox is None and meta["corners"]:
            lats = [v for k, v in meta["corners"].items() if "lat" in k]
            lons = [v for k, v in meta["corners"].items() if "lon" in k]
            if lats and lons:
                bbox = {
                    "lat_min": min(lats),
                    "lat_max": max(lats),
                    "lon_min": min(lons),
                    "lon_max": max(lons),
                }

        product = {
            "product_id": product_dir,
            "sensor": sensor_name,
            "img_path": os.path.relpath(img_path, ROOT).replace("\\", "/"),
            "xml_path": os.path.relpath(xml_path, ROOT).replace("\\", "/"),
            "geometry_csv": (
                os.path.relpath(geo_csv, ROOT).replace("\\", "/")
                if geo_csv
                else None
            ),
            "width": meta["width"],
            "height": meta["height"],
            "dtype": meta["dtype"],
            "data_type_pds4": meta["data_type_pds4"],
            "pixel_resolution_m": meta["pixel_resolution_m"],
            "corners": meta["corners"],
            "bounding_box": bbox,
            "projection": meta["projection"],
            "area": meta["area"],
            "file_size_bytes": meta["file_size_bytes"],
        }
        products.append(product)
        print(f"  [OK] {product_dir}  {meta['width']}x{meta['height']}  {meta['dtype']}  {meta['pixel_resolution_m']} m/px")

    return products


def main():
    print("=" * 60)
    print("Building product catalog from downloaded images")
    print("=" * 60)

    all_products = []

    for sensor_dir, sensor_name in [
        (os.path.join(DOWNLOAD_DIR, "ohrc"), "OHRC"),
        (os.path.join(DOWNLOAD_DIR, "tmc-2"), "TMC-2"),
    ]:
        if not os.path.isdir(sensor_dir):
            print(f"\n[SKIP] Directory not found: {sensor_dir}")
            continue
        print(f"\nScanning {sensor_name} products in {sensor_dir}...")
        products = discover_products(sensor_dir, sensor_name)
        all_products.extend(products)
        print(f"  Found {len(products)} {sensor_name} products")

    catalog = {
        "build_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "total_products": len(all_products),
        "ohrc_count": sum(1 for p in all_products if p["sensor"] == "OHRC"),
        "tmc2_count": sum(1 for p in all_products if p["sensor"] == "TMC-2"),
        "products": all_products,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Catalog written to: {OUTPUT_FILE}")
    print(f"Total products: {catalog['total_products']}")
    print(f"  OHRC: {catalog['ohrc_count']}")
    print(f"  TMC-2: {catalog['tmc2_count']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
