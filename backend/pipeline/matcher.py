"""
ChandraMatch Feature Matcher (Module B6)

Provides feature matching for SIFT descriptors using OpenCV BFMatcher (L2) or
FlannBasedMatcher (KD-Tree), Lowe's ratio test filtering, zero-feature safety,
descriptor validation, and strict split isolation.
"""
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import cv2


class FeatureMatcher:
    """
    Feature matching engine for SIFT descriptors across tile pairs.
    """

    def __init__(
        self,
        method: str = "bf",
        ratio_threshold: float = 0.75,
        cross_check: bool = False,
    ):
        """
        Parameters
        ----------
        method : str, optional
            Matching algorithm: 'bf' (Brute-Force L2) or 'flann' (KD-Tree). Default is 'bf'.
        ratio_threshold : float, optional
            Lowe's ratio test distance threshold. Default is 0.75.
        cross_check : bool, optional
            Whether to enable crossCheck in BFMatcher. Default is False.
            (Must remain False when performing k=2 kNN Lowe ratio matching).
        """
        self.method = method.lower()
        if self.method not in ("bf", "flann"):
            raise ValueError(f"Unsupported matching method: '{method}'. Must be 'bf' or 'flann'.")

        self.ratio_threshold = float(ratio_threshold)
        self.cross_check = bool(cross_check)

        # Initialize matcher instances
        if self.method == "bf":
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=self.cross_check)
        else:  # 'flann'
            # FLANN_INDEX_KDTREE = 1 for float32 SIFT descriptors
            index_params = dict(algorithm=1, trees=5)
            search_params = dict(checks=50)
            self.matcher = cv2.FlannBasedMatcher(index_params, search_params)

    def validate_descriptors(
        self, descriptors: Any
    ) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Validate and normalize input descriptor array.

        Returns
        -------
        (is_valid, normalized_array, status_code)
        """
        if descriptors is None:
            return False, None, "ZERO_FEATURES"

        if not isinstance(descriptors, np.ndarray):
            try:
                descriptors = np.asarray(descriptors)
            except Exception:
                return False, None, "INVALID_DESCRIPTORS"

        if descriptors.size == 0:
            return False, None, "ZERO_FEATURES"

        if descriptors.ndim != 2:
            return False, None, "INVALID_DESCRIPTORS"

        if descriptors.shape[1] != 128:
            return False, None, "INVALID_DESCRIPTORS"

        if not np.issubdtype(descriptors.dtype, np.number):
            return False, None, "INVALID_DESCRIPTORS"

        # Ensure float32 dtype for SIFT matching
        if descriptors.dtype != np.float32:
            try:
                descriptors = descriptors.astype(np.float32)
            except Exception:
                return False, None, "INVALID_DESCRIPTORS"

        if descriptors.shape[0] < 1:
            return False, None, "ZERO_FEATURES"

        return True, descriptors, "SUCCESS"

    def match_descriptors(
        self,
        desc_a: Any,
        desc_b: Any,
        kps_a: Optional[List[cv2.KeyPoint]] = None,
        kps_b: Optional[List[cv2.KeyPoint]] = None,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
        split_a: Optional[str] = None,
        split_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Match two sets of descriptors and keypoints directly.
        """
        # Split isolation enforcement
        if split_a is not None and split_b is not None:
            norm_split_a = str(split_a).strip().lower()
            norm_split_b = str(split_b).strip().lower()
            if norm_split_a != norm_split_b:
                raise ValueError(
                    f"Cross-split matching prohibited: Tile A split '{split_a}' vs Tile B split '{split_b}'"
                )

        # Validate Tile A descriptors
        valid_a, clean_desc_a, status_a = self.validate_descriptors(desc_a)
        if not valid_a:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status=status_a
            )

        # Validate Tile B descriptors
        valid_b, clean_desc_b, status_b = self.validate_descriptors(desc_b)
        if not valid_b:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status=status_b
            )

        # If either set has fewer than 2 descriptors, k=2 knnMatch cannot produce 2 neighbors
        if clean_desc_a.shape[0] < 2 or clean_desc_b.shape[0] < 2:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status="INSUFFICIENT_MATCHES"
            )

        # Validate keypoints count consistency if keypoints are provided
        kps_a_list = kps_a if kps_a is not None else []
        kps_b_list = kps_b if kps_b is not None else []

        if kps_a is not None and len(kps_a_list) != clean_desc_a.shape[0]:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status="INVALID_DESCRIPTORS"
            )

        if kps_b is not None and len(kps_b_list) != clean_desc_b.shape[0]:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status="INVALID_DESCRIPTORS"
            )

        # Perform kNN matching (k=2) safely
        try:
            knn_matches = self.matcher.knnMatch(clean_desc_a, clean_desc_b, k=2)
        except Exception:
            return self._build_zero_response(
                tile_a_id, tile_b_id, status="MATCHING_ERROR"
            )

        tentative_count = len(knn_matches)
        filtered_matches: List[cv2.DMatch] = []

        # Apply Lowe's ratio test safely
        for match_pair in knn_matches:
            if len(match_pair) < 2:
                continue
            m, n = match_pair[0], match_pair[1]
            if m.distance < self.ratio_threshold * n.distance:
                filtered_matches.append(m)

        filtered_count = len(filtered_matches)

        # Extract coordinates for filtered matches if keypoints were provided
        if filtered_count > 0 and len(kps_a_list) > 0 and len(kps_b_list) > 0:
            try:
                src_pts = np.float32(
                    [kps_a_list[m.queryIdx].pt for m in filtered_matches]
                ).reshape(-1, 2)
                dst_pts = np.float32(
                    [kps_b_list[m.trainIdx].pt for m in filtered_matches]
                ).reshape(-1, 2)
            except (IndexError, AttributeError):
                return self._build_zero_response(
                    tile_a_id, tile_b_id, status="INVALID_DESCRIPTORS"
                )
        else:
            src_pts = np.empty((0, 2), dtype=np.float32)
            dst_pts = np.empty((0, 2), dtype=np.float32)

        status = "SUCCESS" if filtered_count > 0 else "INSUFFICIENT_MATCHES"

        return {
            "tentative_matches_count": tentative_count,
            "filtered_matches_count": filtered_count,
            "src_pts": src_pts,
            "dst_pts": dst_pts,
            "lowe_ratio": self.ratio_threshold,
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "matches": filtered_matches,
            "status": status,
        }

    def match_features(
        self,
        features_a: Dict[str, Any],
        features_b: Dict[str, Any],
        split_a: Optional[str] = None,
        split_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Primary interface matching two B5 feature dictionaries.

        Parameters
        ----------
        features_a : dict
            B5 feature extraction result for Tile A.
        features_b : dict
            B5 feature extraction result for Tile B.
        split_a : str, optional
            Dataset split tag for Tile A ('train', 'val', 'test').
        split_b : str, optional
            Dataset split tag for Tile B ('train', 'val', 'test').

        Returns
        -------
        dict
            Matching result dictionary.
        """
        if not isinstance(features_a, dict) or not isinstance(features_b, dict):
            tile_a_id = features_a.get("tile_id") if isinstance(features_a, dict) else None
            tile_b_id = features_b.get("tile_id") if isinstance(features_b, dict) else None
            return self._build_zero_response(
                tile_a_id, tile_b_id, status="INVALID_DESCRIPTORS"
            )

        tile_a_id = features_a.get("tile_id")
        tile_b_id = features_b.get("tile_id")

        kps_a = features_a.get("keypoints")
        kps_b = features_b.get("keypoints")

        desc_a = features_a.get("descriptors")
        desc_b = features_b.get("descriptors")

        return self.match_descriptors(
            desc_a=desc_a,
            desc_b=desc_b,
            kps_a=kps_a,
            kps_b=kps_b,
            tile_a_id=tile_a_id,
            tile_b_id=tile_b_id,
            split_a=split_a,
            split_b=split_b,
        )

    def _build_zero_response(
        self,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
        status: str = "ZERO_FEATURES",
    ) -> Dict[str, Any]:
        """Helper to construct safe zero-match response."""
        return {
            "tentative_matches_count": 0,
            "filtered_matches_count": 0,
            "src_pts": np.empty((0, 2), dtype=np.float32),
            "dst_pts": np.empty((0, 2), dtype=np.float32),
            "lowe_ratio": self.ratio_threshold,
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "matches": [],
            "status": status,
        }
