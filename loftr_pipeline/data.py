"""Manifest-driven raw tile assembly and cached, revision-pinned HF downloads."""
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import logging
from pathlib import Path, PurePosixPath

import numpy as np
from huggingface_hub import HfApi, hf_hub_download

LOG = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def safe_relative(value):
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError(f"Unsafe dataset path: {value}")
    return path.as_posix()


class TileStore:
    def __init__(self, repo_id="akshitjn/my-large-dataset", revision="main",
                 cache_dir=None, local_root=None, offline=False):
        self.repo_id = repo_id
        self.cache_dir = str(cache_dir or ROOT / "dataset/loftr_cache")
        self.local_root = Path(local_root).resolve() if local_root else None
        self.offline = offline
        if offline and not self.local_root:
            raise ValueError("Offline mode requires a local dataset root")
        if offline:
            self.revision = None
        else:
            try:
                self.revision = HfApi().dataset_info(repo_id, revision=revision).sha
            except Exception:
                if self.local_root:
                    LOG.warning("HF unreachable; falling back to local-only mode")
                    self.offline = True
                    self.revision = None
                else:
                    raise
        self.manifest = json.loads(self.fetch("streaming_dataset/dataset_manifest.json").read_text(encoding="utf-8-sig"))
        with self.fetch("ground_truth/manifests/pairs.csv").open(encoding="utf-8-sig", newline="") as f:
            self.pairs = list(csv.DictReader(f))
        catalog = json.loads(self.fetch("ground_truth/product_catalog.json").read_text(encoding="utf-8-sig"))
        self.products = {p["product_id"]: p for p in catalog["products"]}
        records = self.manifest["tiles"]
        self.records = list(records.values()) if isinstance(records, dict) else records
        self.by_product = {}
        for record in self.records:
            self.by_product.setdefault(record["product_id"], []).append(record)
        self.downloaded_tiles = 0
        self.local_tiles = 0

    def fetch(self, relative):
        relative = safe_relative(relative)
        if self.local_root:
            local = self.local_root / relative
            if local.is_file():
                return local
            alt = self.local_root / "dataset" / relative
            if alt.is_file():
                return alt
        if self.offline:
            raise FileNotFoundError(f"Missing local dataset file: {relative}")
        return Path(hf_hub_download(self.repo_id, relative, repo_type="dataset",
                                   revision=self.revision, cache_dir=self.cache_dir))

    @staticmethod
    def _source_ref_ids(pair):
        src = pair.get("source_product_id") or pair.get("ohrc_product_id")
        ref = pair.get("reference_product_id") or pair.get("tmc2_product_id")
        return src, ref

    def pair(self, pair_id):
        for pair in self.pairs:
            if pair["pair_id"] == pair_id:
                src, ref = self._source_ref_ids(pair)
                for pid in (src, ref):
                    if pid not in self.by_product:
                        raise ValueError(f"{pair_id}: product {pid} has no tiles in this manifest")
                return pair
        raise ValueError(f"Unknown pair: {pair_id}")

    def available_pairs(self):
        out = []
        for p in self.pairs:
            src, ref = self._source_ref_ids(p)
            out.append({**p, "tiles_available": src in self.by_product and ref in self.by_product})
        return out

    def assemble(self, product_id, roi, workers=6):
        """Return raw float32 pixels and validity mask; fail on missing tile coverage.

        ROI is x, y, width, height in zero-based native product pixels.
        Existing masks are preserved; zero intensity itself is not assumed invalid.
        """
        x, y, width, height = map(int, roi)
        product = self.products[product_id]
        if min(x, y) < 0 or min(width, height) <= 0 or x + width > product["width"] or y + height > product["height"]:
            raise ValueError(f"ROI outside {product_id}: {roi}")
        if width * height > 160_000_000:
            raise ValueError("ROI exceeds the 160 million native pixel memory limit")
        records = [t for t in self.by_product.get(product_id, [])
                   if t["source_col_start"] < x + width and t["source_col_end"] > x
                   and t["source_row_start"] < y + height and t["source_row_end"] > y]
        if not records:
            raise ValueError("No tiles cover the requested region")
        LOG.info("Assembling %s ROI %s from %d tiles", product_id, roi, len(records))
        # Download only paths concurrently; never retain hundreds of raw tiles in RAM.
        def locate(t):
            return self.fetch("streaming_dataset/" + safe_relative(t["rel_filepath"]))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            paths = list(pool.map(locate, records))
        raw = np.zeros((height, width), np.float32)
        valid = np.zeros((height, width), np.uint8)
        covered = np.zeros((height, width), bool)
        for record, path in zip(records, paths):
            tx, ty = record["source_col_start"], record["source_row_start"]
            shape = (record["source_row_end"] - ty, record["source_col_end"] - tx)
            with np.load(path, allow_pickle=False) as tile:
                a, mask = tile["raw"], tile["mask"]
                if a.shape != shape or mask.shape != shape or a.dtype.kind not in "uif":
                    raise ValueError(f"Invalid tile arrays: {path.name}")
                x0, y0 = max(x, tx), max(y, ty)
                x1, y1 = min(x + width, tx + shape[1]), min(y + height, ty + shape[0])
                src = np.s_[y0 - ty:y1 - ty, x0 - tx:x1 - tx]
                dst = np.s_[y0 - y:y1 - y, x0 - x:x1 - x]
                values = a[src].astype(np.float32)
                raw[dst] = np.nan_to_num(values)
                valid[dst] = ((mask[src] > 0) & np.isfinite(values)).astype(np.uint8) * 255
                covered[dst] = True
        if not covered.all():
            raise ValueError(f"Incomplete tile coverage: {int((~covered).sum())} missing pixels")
        return raw, valid


def centered_roi(width, height, side=8192, center=None):
    w, h = min(side, width), min(side, height)
    cx, cy = center or (width / 2, height / 2)
    x = max(0, min(width - w, int(round(cx - w / 2))))
    y = max(0, min(height - h, int(round(cy - h / 2))))
    return [x, y, w, h]
