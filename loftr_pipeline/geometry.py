"""Coarse alignment from geolocation grids, never used as accuracy ground truth."""
import csv
from pathlib import Path

import cv2
import numpy as np
from huggingface_hub import HfApi, hf_hub_download
from scipy.spatial import cKDTree

from .data import safe_relative


def transform_points(matrix, points):
    p = np.asarray(points, np.float64).reshape(-1, 2)
    q = np.c_[p, np.ones(len(p))] @ np.asarray(matrix).T
    if np.any(np.abs(q[:, 2]) < 1e-10):
        raise ValueError("Transformation maps points to infinity")
    return q[:, :2] / q[:, 2:]


def translation(x, y):
    return np.array([[1., 0., x], [0., 1., y], [0., 0., 1.]])


def resize_matrix(old_width, old_height, new_width, new_height):
    # OpenCV uses pixel-centre coordinates: x_new = (x_old + .5) * scale - .5.
    sx, sy = new_width / old_width, new_height / old_height
    return np.array([[sx, 0., (sx - 1) / 2], [0., sy, (sy - 1) / 2], [0., 0., 1.]])


def lonlat_xyz(lonlat):
    lon, lat = np.deg2rad(np.asarray(lonlat).T)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)


class GeoGrid:
    def __init__(self, path):
        with Path(path).open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        data = np.array([[float(r[k]) for k in ("Pixel", "Scan", "Longitude", "Latitude")] for r in rows])
        data = data[np.isfinite(data).all(1)]
        if len(data) < 16:
            raise ValueError("Geometry grid has too few valid points")
        self.pixels, self.lonlat = data[:, :2], data[:, 2:]
        self.pixel_tree = cKDTree(self.pixels)
        self.xyz = lonlat_xyz(self.lonlat)
        self.geo_tree = cKDTree(self.xyz)

    def pixel_to_lonlat(self, points):
        result = []
        for p in points:
            _, idx = self.pixel_tree.query(p, k=16)
            xy = self.pixels[idx] - p
            ll = self.lonlat[idx].copy()
            anchor = ll[0, 0]
            ll[:, 0] = anchor + (ll[:, 0] - anchor + 180) % 360 - 180
            coefficients = np.linalg.lstsq(np.c_[xy, np.ones(len(xy))], ll, rcond=None)[0]
            result.append(coefficients[-1])
        return np.asarray(result)

    def lonlat_to_pixel(self, points, max_distance_m=3000):
        result = []
        for ll, xyz in zip(points, lonlat_xyz(points)):
            distance, idx = self.geo_tree.query(xyz, k=16)
            if distance[0] * 1_737_400 > max_distance_m:
                raise ValueError("No nearby TMC-2 geolocation samples for this OHRC ROI")
            neighbors = self.lonlat[idx]
            dx = ((neighbors[:, 0] - ll[0] + 180) % 360 - 180) * np.cos(np.deg2rad(ll[1]))
            dy = neighbors[:, 1] - ll[1]
            design = np.c_[dx, dy, np.ones(len(dx))]
            if np.linalg.matrix_rank(design) < 3:
                raise ValueError("Degenerate local geometry grid")
            result.append(np.linalg.lstsq(design, self.pixels[idx], rcond=None)[0][-1])
        return np.asarray(result)


def fetch_grid(product, store, geometry_repo="Nezaal/pradan-dataset", revision="main"):
    rel = safe_relative(product["geometry_csv"])
    if store.local_root and (store.local_root / rel).is_file():
        return store.local_root / rel, {"source": "local", "path": rel}
    if store.offline:
        raise FileNotFoundError(f"Offline geometry missing: {rel}; provide explicit ROIs instead")
    # Image tiles remain in the user's repo; only source geolocation CSVs come here.
    rel = rel.removeprefix("dataset/pradan_downloads/")
    sha = HfApi().dataset_info(geometry_repo, revision=revision).sha
    path = hf_hub_download(geometry_repo, rel, repo_type="dataset", revision=sha, cache_dir=store.cache_dir)
    return Path(path), {"repo_id": geometry_repo, "revision": sha, "path": rel}


def locate_reference(source_roi, source_grid, reference_grid, reference_product, margin=128):
    x, y, w, h = source_roi
    xx, yy = np.meshgrid(np.linspace(x, x + w - 1, 5), np.linspace(y, y + h - 1, 5))
    source = np.c_[xx.ravel(), yy.ravel()]
    target = reference_grid.lonlat_to_pixel(source_grid.pixel_to_lonlat(source))
    # This is a local approximate geolocation fit, not image registration.
    coeff = np.linalg.lstsq(np.c_[source - source.mean(0), np.ones(len(source))], target, rcond=None)[0]
    matrix = np.eye(3)
    matrix[:2, :2] = coeff[:2].T
    matrix[:2, 2] = coeff[2] - matrix[:2, :2] @ source.mean(0)
    residual = np.linalg.norm(transform_points(matrix, source) - target, axis=1)
    if np.max(residual) > 32:
        raise ValueError("Geometry is too nonlinear for this ROI; use a smaller OHRC window")
    lo = np.floor(target.min(0) - margin).astype(int)
    hi = np.ceil(target.max(0) + margin + 1).astype(int)
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, [reference_product["width"], reference_product["height"]])
    size = hi - lo
    if min(size) < 64 or max(size) > 4096:
        raise ValueError("Predicted reference window is empty or too large; inspect geometry/ROI")
    return [int(lo[0]), int(lo[1]), int(size[0]), int(size[1])], matrix, float(np.sqrt(np.mean(residual ** 2)))


def normalize(raw, mask, clahe=False):
    values = raw[mask > 0]
    if values.size < 256:
        raise ValueError("Too few valid image pixels")
    # Bounded deterministic percentile sample for large mosaics.
    values = values[::max(1, values.size // 1_000_000)]
    low, high = np.percentile(values, [2, 98])
    if high <= low:
        raise ValueError("Image region has no usable intensity contrast")
    image = np.clip((raw - low) * (255 / (high - low)), 0, 255).astype(np.uint8)
    if clahe:
        image = cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8)).apply(image)
    image[mask == 0] = 0
    return image
