"""
ChandraMatch Tile Pair Selector (Module B3)

Provides deterministic, metadata-only spatial tile-pair selection from dataset_manifest.json.
Identifies spatially adjacent (horizontal/vertical) and genuinely overlapping tile pairs
within the same product_id while strictly enforcing dataset split isolation.
"""
import os
import json
from typing import Dict, Any, List, Optional, Set, Tuple


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_MANIFEST = os.path.join(ROOT, "dataset", "streaming_dataset", "dataset_manifest.json")


class TilePairSelector:
    """
    Metadata-only tile pair selector engine for Chandrayaan-2 lunar tile datasets.
    """

    def __init__(
        self,
        manifest_path: Optional[str] = None,
        split: Optional[str] = None,
        dataset_root: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        manifest_path : str, optional
            Path to dataset_manifest.json. Defaults to dataset/streaming_dataset/dataset_manifest.json.
        split : str, optional
            Filter split: 'train', 'val', 'test', or None/'all'.
        dataset_root : str, optional
            Path to dataset root directory.
        """
        if manifest_path is None:
            manifest_path = DEFAULT_MANIFEST
        self.manifest_path = os.path.abspath(manifest_path)

        if dataset_root is None:
            dataset_root = os.path.dirname(self.manifest_path)
        self.dataset_root = os.path.abspath(dataset_root)

        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")

        # Load metadata ONCE on initialization (zero pixel array loading)
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        raw_tiles = manifest_data.get("tiles", manifest_data)
        if isinstance(raw_tiles, dict):
            records = list(raw_tiles.values())
        elif isinstance(raw_tiles, list):
            records = raw_tiles
        else:
            records = []

        all_records = [rec for rec in records if isinstance(rec, dict) and "tile_id" in rec]
        self.tile_map: Dict[str, Dict[str, Any]] = {rec["tile_id"]: rec for rec in all_records}

        self.split_filter = split.lower().strip() if split and split.lower().strip() != "all" else None

        if self.split_filter:
            self.records = [
                rec for rec in all_records
                if (rec.get("dataset_split") or rec.get("split", "")).lower().strip() == self.split_filter
            ]
        else:
            self.records = list(all_records)

    def __len__(self) -> int:
        """Return the number of metadata records loaded in the current split selection."""
        return len(self.records)

    def get_tile_metadata(self, tile_id: str) -> Optional[Dict[str, Any]]:
        """Return full metadata dictionary for a specific tile_id."""
        return self.tile_map.get(tile_id)

    def select_adjacent_pairs(self) -> List[Dict[str, Any]]:
        """Select deterministic pairs of spatially adjacent tiles."""
        return self.select_pairs(mode="adjacent")

    def select_overlapping_pairs(self) -> List[Dict[str, Any]]:
        """Select deterministic pairs of tiles with genuine spatial overlap (intersection_area > 0)."""
        return self.select_pairs(mode="overlap")

    def select_pairs(
        self,
        mode: str = "adjacent",
        max_pairs_per_product: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for tile pair selection.

        Parameters
        ----------
        mode : str, optional
            Selection mode: 'adjacent', 'overlap', or 'all'. Default is 'adjacent'.
        max_pairs_per_product : int, optional
            Optional maximum pairs limit per product_id.

        Returns
        -------
        list of dict
            Standardized tile pair metadata objects.
        """
        mode_norm = (mode or "adjacent").lower().strip()
        if mode_norm not in ("adjacent", "overlap", "all"):
            raise ValueError(f"Unsupported selection mode: '{mode}'. Must be 'adjacent', 'overlap', or 'all'.")

        # Group records by (product_id, dataset_split) for strict product & split isolation
        group_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for rec in self.records:
            prod_id = rec.get("product_id", "unknown")
            split_tag = (rec.get("dataset_split") or rec.get("split", "unknown")).lower().strip()
            key = (prod_id, split_tag)
            if key not in group_map:
                group_map[key] = []
            group_map[key].append(rec)

        selected_pairs: List[Dict[str, Any]] = []

        # Sort group keys deterministically
        sorted_group_keys = sorted(group_map.keys())

        for key in sorted_group_keys:
            prod_records = group_map[key]
            prod_pairs = self._select_pairs_for_group(prod_records, mode=mode_norm)

            if max_pairs_per_product is not None and max_pairs_per_product > 0:
                prod_pairs = prod_pairs[:max_pairs_per_product]

            selected_pairs.extend(prod_pairs)

        # Final deterministic sorting by (product_id, dataset_split, relation, tile_a_id, tile_b_id)
        selected_pairs.sort(
            key=lambda p: (
                p["product_id"],
                p["dataset_split"],
                p["relation"],
                p["tile_a_id"],
                p["tile_b_id"],
            )
        )

        return selected_pairs

    def _select_pairs_for_group(
        self,
        records: List[Dict[str, Any]],
        mode: str = "adjacent",
    ) -> List[Dict[str, Any]]:
        """
        Select tile pairs within a single product and split group using spatial metadata algorithms.
        """
        if len(records) < 2:
            return []

        # Sort records deterministically by row_start, col_start, tile_id
        sorted_records = sorted(
            records,
            key=lambda r: (
                r.get("source_row_start", 0),
                r.get("source_col_start", 0),
                r.get("tile_id", ""),
            ),
        )

        # Build index map: (row_start, col_start) -> tile_record for O(N) adjacency lookup
        coord_map: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for rec in sorted_records:
            r_start = rec.get("source_row_start")
            c_start = rec.get("source_col_start")
            if r_start is not None and c_start is not None:
                coord_map[(r_start, c_start)] = rec

        seen_pair_keys: Set[Tuple[str, str]] = set()
        pairs: List[Dict[str, Any]] = []

        for rec_a in sorted_records:
            tile_a_id = rec_a["tile_id"]
            prod_a = rec_a.get("product_id")
            split_a = (rec_a.get("dataset_split") or rec_a.get("split", "")).lower().strip()

            r1a = rec_a.get("source_row_start")
            r2a = rec_a.get("source_row_end")
            c1a = rec_a.get("source_col_start")
            c2a = rec_a.get("source_col_end")

            if r1a is None or r2a is None or c1a is None or c2a is None:
                continue

            # 1. Check Horizontal Adjacency: Tile B starts at (r1a, c2a)
            if mode in ("adjacent", "all"):
                rec_b = coord_map.get((r1a, c2a))
                if rec_b and rec_b.get("source_row_end") == r2a:
                    self._add_pair_if_valid(
                        rec_a, rec_b, "horizontal_adjacent", seen_pair_keys, pairs
                    )

                # Check Vertical Adjacency: Tile B starts at (r2a, c1a)
                rec_b = coord_map.get((r2a, c1a))
                if rec_b and rec_b.get("source_col_end") == c2a:
                    self._add_pair_if_valid(
                        rec_a, rec_b, "vertical_adjacent", seen_pair_keys, pairs
                    )

            # 2. Check Spatial Overlap (intersection_area > 0, excluding border touching)
            if mode in ("overlap", "all"):
                for rec_b in sorted_records:
                    if rec_a["tile_id"] == rec_b["tile_id"]:
                        continue

                    r1b = rec_b.get("source_row_start")
                    r2b = rec_b.get("source_row_end")
                    c1b = rec_b.get("source_col_start")
                    c2b = rec_b.get("source_col_end")

                    if r1b is not None and r2b is not None and c1b is not None and c2b is not None:
                        row_overlap = max(0, min(r2a, r2b) - max(r1a, r1b))
                        col_overlap = max(0, min(c2a, c2b) - max(c1a, c1b))
                        intersection_area = row_overlap * col_overlap

                        if intersection_area > 0:
                            self._add_pair_if_valid(
                                rec_a, rec_b, "overlap", seen_pair_keys, pairs
                            )

        return pairs

    def _add_pair_if_valid(
        self,
        rec_a: Dict[str, Any],
        rec_b: Dict[str, Any],
        relation_type: str,
        seen_pair_keys: Set[Tuple[str, str]],
        pairs_list: List[Dict[str, Any]],
    ):
        """Validate split and product isolation, apply canonical deduplication, and record pair."""
        id_a = rec_a["tile_id"]
        id_b = rec_b["tile_id"]

        if id_a == id_b:
            return

        prod_a = rec_a.get("product_id")
        prod_b = rec_b.get("product_id")
        if prod_a != prod_b:
            raise ValueError(f"Cross-product pair violation: '{prod_a}' vs '{prod_b}'")

        split_a = (rec_a.get("dataset_split") or rec_a.get("split", "")).lower().strip()
        split_b = (rec_b.get("dataset_split") or rec_b.get("split", "")).lower().strip()
        if split_a != split_b:
            raise ValueError(f"Cross-split pair violation: '{split_a}' vs '{split_b}'")

        # Canonical unordered pair key to prevent (A, B) and (B, A) duplicates
        if id_a < id_b:
            pair_key = (id_a, id_b)
            first_rec, second_rec = rec_a, rec_b
        else:
            pair_key = (id_b, id_a)
            first_rec, second_rec = rec_b, rec_a

        if pair_key in seen_pair_keys:
            return
        seen_pair_keys.add(pair_key)

        pairs_list.append(
            {
                "tile_a_id": first_rec["tile_id"],
                "tile_b_id": second_rec["tile_id"],
                "product_id": prod_a,
                "dataset_split": split_a,
                "relation": relation_type,
                "relationship": relation_type,  # Alias key for backward compatibility
                "tile_a": first_rec,
                "tile_b": second_rec,
                "tile_a_record": first_rec,     # Alias key for backward compatibility
                "tile_b_record": second_rec,     # Alias key for backward compatibility
            }
        )
