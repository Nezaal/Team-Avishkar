"""
ChandraMatch Pipeline Runner (Module B2 + B3 + B5 + B6 + B7 + B8 Orchestrator)

Orchestrates the complete tile-level processing pipeline across:
- B2: OHRCTileDataset (Lazy tile loading)
- B3: TilePairSelector (Metadata pair selection)
- B5: SIFTFeatureExtractor (Feature extraction)
- B6: FeatureMatcher (BF/FLANN Lowe ratio matching)
- B7: RansacEstimator (RANSAC homography estimation)
- B8: ImageRegistration (Perspective warping & metric evaluation)

Maintains full backward compatibility for scene-level pair preprocessing.
"""
import os
import sys
import json
import csv
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAIRS_CSV = os.path.join(ROOT, "ground_truth", "manifests", "pairs.csv")
DEFAULT_MANIFEST = os.path.join(ROOT, "dataset", "streaming_dataset", "dataset_manifest.json")

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.loader import ImageLoader, OHRCTileDataset
from pipeline.pair_analyzer import PairAnalyzer
from pipeline.pair_selector import TilePairSelector
from pipeline.preprocessor import preprocess_image
from pipeline.sift import SiftFeatureExtractor
from pipeline.matcher import FeatureMatcher
from pipeline.ransac import RansacEstimator
from pipeline.registration import ImageRegistration


def load_pairs(pairs_csv=None):
    """Load pairs.csv and return list of dicts."""
    csv_path = pairs_csv or PAIRS_CSV
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_pair(pair_id, pairs_csv=None):
    """Get a specific pair by ID."""
    pairs = load_pairs(pairs_csv)
    for p in pairs:
        if p["pair_id"] == pair_id:
            return p
    raise KeyError(f"Pair not found: {pair_id}")


def crop_tmc2_to_ohrc_extent(tmc2_array, ohrc_height, ohrc_width, tmc2_height, tmc2_width):
    """Crop the TMC-2 image along-track to match the OHRC's extent."""
    ohrc_res = 0.25
    tmc2_res = 4.5
    resolution_ratio = ohrc_res / tmc2_res

    tmc2_lines_needed = int(ohrc_height * resolution_ratio * 1.5)
    tmc2_lines_needed = min(tmc2_lines_needed, tmc2_height)

    if tmc2_lines_needed >= tmc2_height:
        return tmc2_array

    start_line = (tmc2_height - tmc2_lines_needed) // 2
    end_line = start_line + tmc2_lines_needed
    return tmc2_array[start_line:end_line, :]


class PipelineRunner:
    """
    Pipeline Runner for single-pair tile-level processing (B2-B8) and legacy scene preprocessing.
    """

    def __init__(
        self,
        dataset_root: Optional[str] = None,
        manifest_path: Optional[str] = None,
        catalog_path: Optional[str] = None,
        pairs_csv: Optional[str] = None,
        sift_config: Optional[Dict[str, Any]] = None,
        matcher_config: Optional[Dict[str, Any]] = None,
        ransac_config: Optional[Dict[str, Any]] = None,
        registration_config: Optional[Dict[str, Any]] = None,
    ):
        self.manifest_path = os.path.abspath(manifest_path) if manifest_path else DEFAULT_MANIFEST
        self.dataset_root = os.path.abspath(dataset_root) if dataset_root else os.path.dirname(self.manifest_path)
        self.pairs_csv = pairs_csv

        # Initialize core processing modules
        self.loader = ImageLoader(catalog_path)
        self.analyzer = PairAnalyzer()

        sift_cfg = sift_config or {}
        self.extractor = SiftFeatureExtractor(**sift_cfg)

        match_cfg = matcher_config or {}
        self.matcher = FeatureMatcher(**match_cfg)

        ransac_cfg = ransac_config or {}
        self.ransac = RansacEstimator(**ransac_cfg)

        reg_cfg = registration_config or {}
        self.registrator = ImageRegistration(**reg_cfg)

        # Lazy selector instance
        self._selector: Optional[TilePairSelector] = None

    @property
    def selector(self) -> TilePairSelector:
        if self._selector is None:
            self._selector = TilePairSelector(manifest_path=self.manifest_path, dataset_root=self.dataset_root)
        return self._selector

    def get_dataset_info(self) -> Dict[str, Any]:
        """Return dataset metadata summary."""
        meta_tiles = self.selector.records
        train_count = sum(1 for r in meta_tiles if (r.get("dataset_split") or r.get("split", "")).lower() == "train")
        val_count = sum(1 for r in meta_tiles if (r.get("dataset_split") or r.get("split", "")).lower() == "val")
        test_count = sum(1 for r in meta_tiles if (r.get("dataset_split") or r.get("split", "")).lower() == "test")

        return {
            "dataset": "OHRC",
            "total_tiles": len(meta_tiles),
            "splits": {
                "train": train_count,
                "val": val_count,
                "test": test_count,
            },
            "tile_size": [512, 512],
        }

    def _load_tile_sample(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Lazy load single tile .npz file from disk based on manifest metadata."""
        tile_id = meta["tile_id"]
        product_id = meta.get("product_id", "")
        sensor = meta.get("sensor", "OHRC")
        dataset_split = meta.get("dataset_split") or meta.get("split", "unknown")

        rel_path = meta.get("rel_filepath")
        if rel_path:
            norm_rel_path = os.path.normpath(rel_path)
            npz_path = os.path.join(self.dataset_root, norm_rel_path)
        else:
            npz_path = os.path.join(self.dataset_root, "tiles", product_id, f"{tile_id}.npz")

        if not os.path.exists(npz_path):
            raise FileNotFoundError(f"Tile .npz file not found at: {npz_path}")

        with np.load(npz_path) as data:
            raw_arr = np.copy(data["raw"])
            prep_arr = np.copy(data["preprocessed"])
            mask_arr = np.copy(data["mask"])

        return {
            "raw": raw_arr,
            "preprocessed": prep_arr,
            "mask": mask_arr,
            "tile_id": tile_id,
            "product_id": product_id,
            "sensor": sensor,
            "dataset_split": dataset_split,
        }

    def run_pair(
        self,
        tile_a_id: str,
        tile_b_id: str,
        split: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run complete B2 -> B5 -> B6 -> B7 -> B8 pipeline on ONE requested tile pair.

        Parameters
        ----------
        tile_a_id : str
            Identifier for Tile A (Reference).
        tile_b_id : str
            Identifier for Tile B (Moving).
        split : str, optional
            Dataset split tag ('train', 'val', 'test').

        Returns
        -------
        dict
            JSON-serializable standardized pipeline result dictionary.
        """
        # STEP 1: Locate metadata
        meta_a = self.selector.get_tile_metadata(tile_a_id)
        meta_b = self.selector.get_tile_metadata(tile_b_id)

        if not meta_a or not meta_b:
            missing_id = tile_a_id if not meta_a else tile_b_id
            return self._build_pipeline_response(
                status="TILE_NOT_FOUND",
                stage="METADATA_LOOKUP",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                message=f"Tile ID '{missing_id}' not found in manifest database",
            )

        # STEP 2: Validate Product & Split Isolation
        prod_a = meta_a.get("product_id")
        prod_b = meta_b.get("product_id")
        if prod_a != prod_b:
            return self._build_pipeline_response(
                status="CROSS_PRODUCT_PROHIBITED",
                stage="ISOLATION_CHECK",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                message=f"Cross-product pair prohibited: '{prod_a}' vs '{prod_b}'",
            )

        split_a = (meta_a.get("dataset_split") or meta_a.get("split", "")).lower().strip()
        split_b = (meta_b.get("dataset_split") or meta_b.get("split", "")).lower().strip()
        if split_a != split_b:
            return self._build_pipeline_response(
                status="CROSS_SPLIT_PROHIBITED",
                stage="ISOLATION_CHECK",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
                message=f"Cross-split pair prohibited: '{split_a}' vs '{split_b}'",
            )

        # STEP 3 & 4: Lazy load ONLY the two requested tiles from disk
        try:
            sample_a = self._load_tile_sample(meta_a)
            sample_b = self._load_tile_sample(meta_b)
        except Exception as e:
            return self._build_pipeline_response(
                status="TILE_LOAD_ERROR",
                stage="TILE_LOADING",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
                message=f"Failed to load tile files from disk: {str(e)}",
            )

        if not sample_a or not sample_b:
            return self._build_pipeline_response(
                status="TILE_NOT_FOUND",
                stage="TILE_LOADING",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
            )

        # STEP 5: Run B5 SIFT Extraction
        feat_a = self.extractor.extract_from_sample(sample_a)
        feat_b = self.extractor.extract_from_sample(sample_b)

        kps_cnt_a = int(feat_a.get("count", 0))
        kps_cnt_b = int(feat_b.get("count", 0))

        if kps_cnt_a == 0 or kps_cnt_b == 0:
            return self._build_pipeline_response(
                status="ZERO_FEATURES",
                stage="SIFT_EXTRACTION",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
                feat_metrics={"tile_a_keypoints": kps_cnt_a, "tile_b_keypoints": kps_cnt_b},
            )

        # STEP 6: Run B6 Feature Matching
        match_res = self.matcher.match_features(
            feat_a, feat_b, split_a=split_a, split_b=split_b
        )

        tentative_cnt = int(match_res.get("tentative_matches_count", 0))
        filtered_cnt = int(match_res.get("filtered_matches_count", 0))
        lowe_ratio = float(match_res.get("lowe_ratio", 0.75))

        match_metrics = {
            "tentative_matches": tentative_cnt,
            "filtered_matches": filtered_cnt,
            "lowe_ratio": lowe_ratio,
        }

        if match_res.get("status") != "SUCCESS" or filtered_cnt < 4:
            return self._build_pipeline_response(
                status=match_res.get("status", "INSUFFICIENT_MATCHES"),
                stage="FEATURE_MATCHING",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
                feat_metrics={"tile_a_keypoints": kps_cnt_a, "tile_b_keypoints": kps_cnt_b},
                match_metrics=match_metrics,
            )

        # STEP 7: Run B7 RANSAC Estimator
        ransac_res = self.ransac.estimate(match_res)

        in_count = int(ransac_res.get("inlier_count", 0))
        out_count = int(ransac_res.get("outlier_count", 0))
        in_ratio = float(ransac_res.get("inlier_ratio", 0.0))
        in_matches = int(ransac_res.get("input_matches_count", 0))

        ransac_metrics = {
            "input_matches": in_matches,
            "inlier_count": in_count,
            "outlier_count": out_count,
            "inlier_ratio": in_ratio,
        }

        H = ransac_res.get("homography")

        if ransac_res.get("status") != "SUCCESS" or H is None:
            return self._build_pipeline_response(
                status=ransac_res.get("status", "RANSAC_FAILED"),
                stage="RANSAC_ESTIMATION",
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                product_id=prod_a,
                dataset_split=split_a,
                feat_metrics={"tile_a_keypoints": kps_cnt_a, "tile_b_keypoints": kps_cnt_b},
                match_metrics=match_metrics,
                ransac_metrics=ransac_metrics,
            )

        # STEP 8: Run B8 Image Registration & Metric Evaluation
        b8_res = self.registrator.register(
            image_a=sample_a["preprocessed"],
            image_b=sample_b["preprocessed"],
            ransac_result=ransac_res,
            mask_a=sample_a.get("mask"),
            mask_b=sample_b.get("mask"),
            tile_a_id=tile_a_id,
            tile_b_id=tile_b_id,
        )

        reg_metrics_raw = b8_res.get("metrics", {})
        mae_val = float(reg_metrics_raw["mae"]) if reg_metrics_raw.get("mae") is not None else None
        mse_val = float(reg_metrics_raw["mse"]) if reg_metrics_raw.get("mse") is not None else None
        rmse_val = float(reg_metrics_raw["rmse"]) if reg_metrics_raw.get("rmse") is not None else None

        registration_metrics = {
            "mae": mae_val,
            "mse": mse_val,
            "rmse": rmse_val,
            "valid_pixel_count": int(reg_metrics_raw.get("valid_pixel_count", 0)),
            "valid_pixel_ratio": float(reg_metrics_raw.get("valid_pixel_ratio", 0.0)),
        }

        H_list = H.tolist() if isinstance(H, np.ndarray) else None

        # STEP 9: Return standardized JSON-serializable pipeline output
        return self._build_pipeline_response(
            status=b8_res.get("status", "SUCCESS"),
            stage="REGISTRATION",
            tile_a_id=tile_a_id,
            tile_b_id=tile_b_id,
            product_id=prod_a,
            dataset_split=split_a,
            feat_metrics={"tile_a_keypoints": kps_cnt_a, "tile_b_keypoints": kps_cnt_b},
            match_metrics=match_metrics,
            ransac_metrics=ransac_metrics,
            registration_metrics=registration_metrics,
            homography=H_list,
        )

    def run_selected_pair(
        self,
        split: str = "train",
        mode: str = "adjacent",
    ) -> Dict[str, Any]:
        """
        Use B3 to deterministically select ONE tile pair and execute the complete pipeline.
        """
        pair_sel = TilePairSelector(manifest_path=self.manifest_path, split=split, dataset_root=self.dataset_root)
        pairs = pair_sel.select_pairs(mode=mode)
        if not pairs:
            return self._build_pipeline_response(
                status="NO_PAIRS_AVAILABLE",
                stage="PAIR_SELECTION",
                dataset_split=split,
                message=f"No tile pairs found for split '{split}' with mode '{mode}'",
            )

        target_pair = pairs[0]
        return self.run_pair(
            tile_a_id=target_pair["tile_a_id"],
            tile_b_id=target_pair["tile_b_id"],
            split=split,
        )

    def _build_pipeline_response(
        self,
        status: str,
        stage: str,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
        product_id: Optional[str] = None,
        dataset_split: Optional[str] = None,
        feat_metrics: Optional[Dict[str, int]] = None,
        match_metrics: Optional[Dict[str, Any]] = None,
        ransac_metrics: Optional[Dict[str, Any]] = None,
        registration_metrics: Optional[Dict[str, Any]] = None,
        homography: Optional[List[List[float]]] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Helper to construct clean JSON-serializable pipeline output."""
        in_cnt = ransac_metrics.get("inlier_count", 0) if ransac_metrics else 0
        in_ratio = ransac_metrics.get("inlier_ratio", 0.0) if ransac_metrics else 0.0

        if status == "SUCCESS":
            if in_cnt >= 30 and in_ratio >= 0.5:
                reg_quality = "HIGH_CONFIDENCE"
            elif in_cnt >= 10 and in_ratio >= 0.2:
                reg_quality = "MODERATE_CONFIDENCE"
            else:
                reg_quality = "LOW_CONFIDENCE"
        else:
            reg_quality = "UNVERIFIED"

        return {
            "status": status,
            "pipeline_status": "SUCCESS" if status in ("SUCCESS", "EMPTY_VALID_REGION") else "FAILED",
            "registration_status": status,
            "registration_quality": reg_quality,
            "pipeline_stage": stage,
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "product_id": product_id,
            "dataset_split": dataset_split,
            "feature_metrics": feat_metrics or {"tile_a_keypoints": 0, "tile_b_keypoints": 0},
            "matching_metrics": match_metrics or {"tentative_matches": 0, "filtered_matches": 0, "lowe_ratio": 0.75},
            "ransac_metrics": ransac_metrics or {"input_matches": 0, "inlier_count": 0, "outlier_count": 0, "inlier_ratio": 0.0},
            "registration_metrics": registration_metrics or {"mae": None, "mse": None, "rmse": None, "valid_pixel_count": 0, "valid_pixel_ratio": 0.0},
            "homography": homography,
            "message": message,
        }

    # Legacy method for scene-level preprocessing compatibility
    def run_preprocessing(self, pair_id, working_scale=None, apply_clahe=None, clahe_clip=2.0):
        """Run preprocessing pipeline for a single scene pair (legacy)."""
        pair = get_pair(pair_id, self.pairs_csv)
        ohrc_id = pair["ohrc_product_id"]
        tmc2_id = pair["tmc2_product_id"]

        source = self.loader.load(ohrc_id)
        reference = self.loader.load(tmc2_id)
        analysis = self.analyzer.analyze(source, reference)

        ref_cropped = crop_tmc2_to_ohrc_extent(
            reference["array"],
            source["height"],
            source["width"],
            reference["height"],
            reference["width"],
        )
        reference_cropped = {
            "array": ref_cropped,
            "width": reference["width"],
            "height": ref_cropped.shape[0],
            "channels": 1,
            "dtype": reference["dtype"],
            "metadata": reference["metadata"],
        }

        src_scale = working_scale or analysis["source_working_scale"]
        ref_scale = analysis["reference_working_scale"]
        clahe = apply_clahe if apply_clahe is not None else analysis["recommend_clahe"]

        source_preprocessed = preprocess_image(source, working_scale=src_scale, clahe_clip=clahe_clip, apply_clahe=clahe)
        reference_preprocessed = preprocess_image(reference_cropped, working_scale=ref_scale, clahe_clip=clahe_clip, apply_clahe=False)

        return {
            "pair_id": pair_id,
            "pair": pair,
            "analysis": analysis,
            "source_preprocessed": source_preprocessed,
            "reference_preprocessed": reference_preprocessed,
        }


def run_single(pair_id, **kwargs):
    """Convenience function to run preprocessing on a single pair."""
    runner = PipelineRunner()
    return runner.run_preprocessing(pair_id, **kwargs)
