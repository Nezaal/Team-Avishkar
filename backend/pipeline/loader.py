"""
ChandraMatch Image Loader (Module B2)

Loads raw Chandrayaan-2 .img files using memory-mapped I/O.
All metadata comes from the product catalog (no header parsing needed
since .img files are pure raw pixel data).

Usage:
    loader = ImageLoader()
    image = loader.load("ch2_ohr_ncp_20200825T1127278043_d_img_d18")
"""
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOG_FILE = os.path.join(ROOT, "ground_truth", "product_catalog.json")


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


def load_image(product_id, catalog_path=None):
    """Convenience function to load a single image."""
    loader = ImageLoader(catalog_path)
    return loader.load(product_id)


def load_pair(ohrc_id, tmc2_id, catalog_path=None):
    """Convenience function to load an image pair."""
    loader = ImageLoader(catalog_path)
    return loader.load_pair(ohrc_id, tmc2_id)
