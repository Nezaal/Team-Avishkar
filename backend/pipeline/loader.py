"""
ChandraMatch Image Loader (Module B2)

Loads raw Chandrayaan-2 .img files using memory-mapped I/O for local files,
and supports remote window reading over HTTP Range requests for cloud PDS4 datasets.

Usage:
    loader = ImageLoader()
    image = loader.load("ch2_ohr_ncp_20200825T1127278043_d_img_d18")

    # Remote window access:
    window = read_remote_window(img_url, width, height, dtype, r_start, r_end, c_start, c_end)
    metadata = read_remote_metadata(xml_url)
"""
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple, Union

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOG_FILE = os.path.join(ROOT, "ground_truth", "product_catalog.json")


def read_remote_window(
    img_url: str,
    width: int,
    height: int,
    dtype: np.dtype,
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int,
    byte_offset: int = 0,
    timeout: float = 15.0,
) -> np.ndarray:
    """
    Read a requested rectangular window from a remote uncompressed PDS4 .img file
    using HTTP Range requests.

    Parameters
    ----------
    img_url : str
        Direct HTTP/HTTPS URL to the uncompressed .img file.
    width : int
        Image width in pixels (samples).
    height : int
        Image height in pixels (lines).
    dtype : np.dtype
        NumPy data type of the PDS4 raster (e.g. np.dtype('uint8') or np.dtype('<u2')).
    row_start : int
        Starting row index (inclusive, 0-indexed).
    row_end : int
        Ending row index (exclusive, 0-indexed).
    col_start : int
        Starting column index (inclusive, 0-indexed).
    col_end : int
        Ending column index (exclusive, 0-indexed).
    byte_offset : int, optional
        Header byte offset in the remote binary file (default 0).
    timeout : float, optional
        HTTP request timeout in seconds (default 15.0).

    Returns
    -------
    np.ndarray
        2D NumPy array of shape (row_end - row_start, col_end - col_start) containing
        only the requested window pixels.
    """
    # 1. Validation Checks (raise ValueError on invalid inputs before making HTTP request)
    if not img_url or not isinstance(img_url, str):
        raise ValueError("img_url must be a non-empty string")
    
    np_dtype = np.dtype(dtype)
    if np_dtype.itemsize <= 0:
        raise ValueError(f"Invalid dtype itemsize: {np_dtype}")
        
    if width <= 0:
        raise ValueError(f"width ({width}) must be positive")
    if height <= 0:
        raise ValueError(f"height ({height}) must be positive")
    if byte_offset < 0:
        raise ValueError(f"byte_offset ({byte_offset}) cannot be negative")
        
    if row_start < 0:
        raise ValueError(f"row_start ({row_start}) cannot be negative")
    if row_end > height:
        raise ValueError(f"row_end ({row_end}) exceeds image height ({height})")
    if row_start >= row_end:
        raise ValueError(f"row_start ({row_start}) must be strictly less than row_end ({row_end})")
        
    if col_start < 0:
        raise ValueError(f"col_start ({col_start}) cannot be negative")
    if col_end > width:
        raise ValueError(f"col_end ({col_end}) exceeds image width ({width})")
    if col_start >= col_end:
        raise ValueError(f"col_start ({col_start}) must be strictly less than col_end ({col_end})")

    # 2. HTTP Range Calculation (Contiguous row-block request)
    bytes_per_pixel = np_dtype.itemsize
    bytes_per_row = width * bytes_per_pixel
    num_rows = row_end - row_start
    num_cols = col_end - col_start
    expected_bytes = num_rows * bytes_per_row

    start_byte = byte_offset + row_start * bytes_per_row
    end_byte = byte_offset + row_end * bytes_per_row - 1

    import requests
    headers = {"Range": f"bytes={start_byte}-{end_byte}"}
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    try:
        resp = requests.get(img_url, headers=headers, timeout=timeout, allow_redirects=True)
        status_code = resp.status_code
        raw_bytes = resp.content
    except Exception as e:
        raise RuntimeError(f"Remote HTTP request failed: {e}")

    # 3. Response Validation
    if status_code not in (206, 200):
        raise RuntimeError(f"Expected HTTP 206 Partial Content, received status {status_code}. Response: {raw_bytes[:100]}")

    if len(raw_bytes) != expected_bytes:
        raise RuntimeError(
            f"Received byte count mismatch: expected {expected_bytes} bytes for "
            f"{num_rows} rows, but received {len(raw_bytes)} bytes"
        )

    # 4. Decode & Crop
    block_array = np.frombuffer(raw_bytes, dtype=np_dtype).reshape(num_rows, width)
    window_array = block_array[:, col_start:col_end].copy()

    return window_array


def read_remote_metadata(xml_url: str, timeout: float = 15.0) -> Dict[str, Any]:
    """
    Fetch and parse PDS4 XML metadata from a remote URL.

    Parameters
    ----------
    xml_url : str
        Direct HTTP/HTTPS URL to the PDS4 .xml metadata file.
    timeout : float, optional
        HTTP request timeout in seconds (default 15.0).

    Returns
    -------
    dict
        Parsed PDS4 metadata dictionary matching B2 contract conventions.
    """
    if not xml_url or not isinstance(xml_url, str):
        raise ValueError("xml_url must be a non-empty string")

    req = urllib.request.Request(xml_url)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_bytes = resp.read()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch remote XML metadata: {e}")

    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        raise ValueError(f"Malformed PDS4 XML content at {xml_url}: {e}")

    elements = []
    axis_names = []
    data_type = None
    file_offset = 0
    nodata = None
    product_id = None
    sensor = None
    resolution_m = None
    projection = None
    coord_sys = None
    start_time = None
    stop_time = None
    
    ul_lat, ul_lon = None, None
    ur_lat, ur_lon = None, None
    ll_lat, ll_lon = None, None
    lr_lat, lr_lon = None, None

    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        text = (elem.text or "").strip()

        if tag == "elements" and text:
            try:
                elements.append(int(text))
            except ValueError:
                pass
        elif tag == "axis_name" and text:
            axis_names.append(text)
        elif tag == "data_type" and text:
            data_type = text
        elif tag == "offset" and "Array_2D_Image" in (elem.attrib.get("name", "") or ""):
            try:
                file_offset = int(text)
            except ValueError:
                pass
        elif tag in ("invalid_constant", "missing_constant", "saturated_constant") and text:
            nodata = text
        elif tag == "file_name" and text and text.endswith(".img"):
            product_id = text[:-4]
        elif tag == "logical_identifier" and text and not product_id:
            product_id = text.split(":")[-1]
        elif tag == "name" and text:
            lower = text.lower()
            if "high resolution camera" in lower or "ohrc" in lower:
                sensor = "OHRC"
            elif "terrain mapping camera" in lower or "tmc" in lower:
                sensor = "TMC-2"
        elif tag == "pixel_resolution" and text:
            try:
                resolution_m = float(text)
            except ValueError:
                pass
        elif tag == "projection" and text:
            projection = text
        elif tag == "target_name" and text:
            coord_sys = text
        elif tag == "start_date_time" and text:
            start_time = text
        elif tag == "stop_date_time" and text:
            stop_time = text
        elif tag == "upper_left_latitude" and text and ul_lat is None:
            try: ul_lat = float(text)
            except ValueError: pass
        elif tag == "upper_left_longitude" and text and ul_lon is None:
            try: ul_lon = float(text)
            except ValueError: pass
        elif tag == "upper_right_latitude" and text and ur_lat is None:
            try: ur_lat = float(text)
            except ValueError: pass
        elif tag == "upper_right_longitude" and text and ur_lon is None:
            try: ur_lon = float(text)
            except ValueError: pass
        elif tag == "lower_left_latitude" and text and ll_lat is None:
            try: ll_lat = float(text)
            except ValueError: pass
        elif tag == "lower_left_longitude" and text and ll_lon is None:
            try: ll_lon = float(text)
            except ValueError: pass
        elif tag == "lower_right_latitude" and text and lr_lat is None:
            try: lr_lat = float(text)
            except ValueError: pass
        elif tag == "lower_right_longitude" and text and lr_lon is None:
            try: lr_lon = float(text)
            except ValueError: pass

    height = elements[0] if len(elements) > 0 else None
    width = elements[1] if len(elements) > 1 else None

    if width is None or height is None:
        raise ValueError(f"Missing required PDS4 image dimensions in XML: width={width}, height={height}")

    corner_coordinates = None
    if all(v is not None for v in [ul_lat, ul_lon, ur_lat, ur_lon, ll_lat, ll_lon, lr_lat, lr_lon]):
        corner_coordinates = {
            "upper_left": {"lat": ul_lat, "lon": ul_lon},
            "upper_right": {"lat": ur_lat, "lon": ur_lon},
            "lower_left": {"lat": ll_lat, "lon": ll_lon},
            "lower_right": {"lat": lr_lat, "lon": lr_lon},
        }

    timestamps = None
    if start_time or stop_time:
        timestamps = {"start_time": start_time, "stop_time": stop_time}

    return {
        "product_id": product_id,
        "sensor": sensor,
        "width": width,
        "height": height,
        "axes": axis_names if axis_names else ["Line", "Sample"],
        "data_type_pds4": data_type,
        "byte_offset": file_offset,
        "nodata": nodata,
        "resolution_m": resolution_m,
        "projection": projection,
        "coordinate_system": coord_sys or "Moon / Selenographic",
        "corner_coordinates": corner_coordinates,
        "timestamps": timestamps,
    }


class ImageLoader:
    """Load Chandrayaan-2 .img files with memory-mapped I/O."""

    def __init__(self, catalog_path=None):
        """
        Parameters
        ----------
        catalog_path : str, optional
            Path to product_catalog.json. Defaults to ground_truth/product_catalog.json.
        """
        self.catalog_path = catalog_path or CATALOG_FILE
        self._catalog = None

    @property
    def catalog(self):
        if self._catalog is None:
            with open(self.catalog_path, encoding="utf-8") as f:
                self._catalog = json.load(f)
        return self._catalog

    def get_product(self, product_id):
        """Look up a product by ID in the catalog."""
        for p in self.catalog["products"]:
            if p["product_id"] == product_id:
                return p
        raise KeyError(f"Product not found in catalog: {product_id}")

    def load(self, product_id):
        """
        Load an image as a memory-mapped numpy array with metadata.

        Parameters
        ----------
        product_id : str
            The product ID (e.g. "ch2_ohr_ncp_20200825T1127278043_d_img_d18").

        Returns
        -------
        dict
            {
                "array": np.ndarray (2D, memmap),
                "width": int,
                "height": int,
                "channels": 1,
                "dtype": str,
                "metadata": {
                    "product_id": str,
                    "sensor": str,
                    "pixel_resolution_m": float,
                    "corners": dict,
                    "bounding_box": dict,
                    "projection": str,
                    "area": str,
                },
            }
        """
        product = self.get_product(product_id)

        # Resolve image path
        img_path = os.path.join(ROOT, product["img_path"])
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file not found: {img_path}")

        # Determine numpy dtype
        dtype_str = product["dtype"]
        if dtype_str is None:
            raise ValueError(f"Unknown dtype for {product_id}")
        np_dtype = np.dtype(dtype_str)

        # Image dimensions
        width = product["width"]
        height = product["height"]
        if width is None or height is None:
            raise ValueError(f"Missing dimensions for {product_id}: {width}x{height}")

        # Memory-map the raw binary file
        # Chandrayaan-2 .img files: row-major, no header, starts at byte 0
        array = np.memmap(img_path, dtype=np_dtype, mode="r", shape=(height, width))

        # Build metadata
        metadata = {
            "product_id": product_id,
            "sensor": product.get("sensor"),
            "pixel_resolution_m": product.get("pixel_resolution_m"),
            "corners": product.get("corners", {}),
            "bounding_box": product.get("bounding_box", {}),
            "projection": product.get("projection"),
            "area": product.get("area"),
            "data_type_pds4": product.get("data_type_pds4"),
            "file_size_bytes": product.get("file_size_bytes"),
        }

        return {
            "array": array,
            "width": width,
            "height": height,
            "channels": 1,
            "dtype": dtype_str,
            "metadata": metadata,
        }

    def load_pair(self, ohrc_product_id, tmc2_product_id):
        """
        Load both images for an OHRC/TMC-2 pair.

        Returns
        -------
        tuple of (source_dict, reference_dict)
        """
        source = self.load(ohrc_product_id)
        reference = self.load(tmc2_product_id)
        return source, reference

    def list_products(self, sensor=None):
        """List all products, optionally filtered by sensor."""
        products = self.catalog["products"]
        if sensor:
            products = [p for p in products if p["sensor"] == sensor]
        return [(p["product_id"], p["sensor"], p["width"], p["height"], p["dtype"]) for p in products]

    def read_remote_window(
        self,
        img_url: str,
        width: int,
        height: int,
        dtype: np.dtype,
        row_start: int,
        row_end: int,
        col_start: int,
        col_end: int,
        byte_offset: int = 0,
        timeout: float = 15.0,
    ) -> np.ndarray:
        """Instance method wrapper for read_remote_window."""
        return read_remote_window(
            img_url=img_url,
            width=width,
            height=height,
            dtype=dtype,
            row_start=row_start,
            row_end=row_end,
            col_start=col_start,
            col_end=col_end,
            byte_offset=byte_offset,
            timeout=timeout,
        )

    def read_remote_metadata(self, xml_url: str, timeout: float = 15.0) -> Dict[str, Any]:
        """Instance method wrapper for read_remote_metadata."""
        return read_remote_metadata(xml_url=xml_url, timeout=timeout)


def load_image(product_id, catalog_path=None):
    """Convenience function to load a single image."""
    loader = ImageLoader(catalog_path)
    return loader.load(product_id)


def load_pair(ohrc_id, tmc2_id, catalog_path=None):
    """Convenience function to load an image pair."""
    loader = ImageLoader(catalog_path)
    return loader.load_pair(ohrc_id, tmc2_id)
