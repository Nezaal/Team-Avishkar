"""
ChandraMatch RANSAC Homography Estimator (Module B7)

Performs geometric verification on matched point correspondences using OpenCV's
RANSAC homography estimation (cv2.findHomography). Identifies geometrically
consistent inlier correspondences, filters outliers, and computes homography matrices safely.
"""
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import cv2


class RansacEstimator:
    """
    RANSAC-based geometric verification and homography estimation engine.
    """

    def __init__(
        self,
        reprojection_threshold: float = 5.0,
        confidence: float = 0.995,
        max_iters: int = 2000,
        min_matches: int = 4,
    ):
        """
        Parameters
        ----------
        reprojection_threshold : float, optional
            Maximum allowed reprojection error in pixels to consider a point as an inlier. Default is 5.0.
        confidence : float, optional
            Desired confidence level for RANSAC (e.g. 0.995). Default is 0.995.
        max_iters : int, optional
            Maximum number of RANSAC iterations. Default is 2000.
        min_matches : int, optional
            Minimum number of point correspondences required to attempt homography estimation. Default is 4.
        """
        self.reprojection_threshold = float(reprojection_threshold)
        self.confidence = float(confidence)
        self.max_iters = int(max_iters)
        self.min_matches = int(min_matches)

    def validate_points(
        self, src_pts: Any, dst_pts: Any
    ) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray], str]:
        """
        Validate and normalize input point correspondence arrays.

        Returns
        -------
        (is_valid, clean_src_pts, clean_dst_pts, status_code)
        """
        if src_pts is None or dst_pts is None:
            return False, None, None, "INVALID_INPUT"

        if not isinstance(src_pts, np.ndarray):
            try:
                src_pts = np.asarray(src_pts)
            except Exception:
                return False, None, None, "INVALID_INPUT"

        if not isinstance(dst_pts, np.ndarray):
            try:
                dst_pts = np.asarray(dst_pts)
            except Exception:
                return False, None, None, "INVALID_INPUT"

        if src_pts.size == 0 and dst_pts.size == 0:
            clean_src = np.empty((0, 2), dtype=np.float32)
            clean_dst = np.empty((0, 2), dtype=np.float32)
            return True, clean_src, clean_dst, "SUCCESS"

        if src_pts.ndim != 2 or dst_pts.ndim != 2:
            return False, None, None, "INVALID_INPUT"

        if src_pts.shape[1] != 2 or dst_pts.shape[1] != 2:
            return False, None, None, "INVALID_INPUT"

        if src_pts.shape[0] != dst_pts.shape[0]:
            return False, None, None, "INVALID_INPUT"

        if not np.issubdtype(src_pts.dtype, np.number) or not np.issubdtype(dst_pts.dtype, np.number):
            return False, None, None, "INVALID_INPUT"

        # Convert safely to float32
        try:
            clean_src = src_pts.astype(np.float32)
            clean_dst = dst_pts.astype(np.float32)
        except Exception:
            return False, None, None, "INVALID_INPUT"

        return True, clean_src, clean_dst, "SUCCESS"

    def estimate_from_points(
        self,
        src_pts: Any,
        dst_pts: Any,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Estimate homography matrix and inliers from source and destination point arrays.

        Parameters
        ----------
        src_pts : array-like
            Nx2 array of source point coordinates in Tile A.
        dst_pts : array-like
            Nx2 array of destination point coordinates in Tile B.
        tile_a_id : str, optional
            Identifier for Tile A.
        tile_b_id : str, optional
            Identifier for Tile B.

        Returns
        -------
        dict
            Standardized RANSAC result dictionary.
        """
        is_valid, clean_src, clean_dst, status_val = self.validate_points(src_pts, dst_pts)
        if not is_valid:
            return self._build_safe_response(
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                input_matches_count=0,
                status=status_val,
            )

        input_matches_count = clean_src.shape[0]

        if input_matches_count < self.min_matches:
            return self._build_safe_response(
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                input_matches_count=input_matches_count,
                status="INSUFFICIENT_MATCHES",
            )

        # Execute cv2.findHomography with RANSAC
        try:
            H, mask = cv2.findHomography(
                clean_src,
                clean_dst,
                method=cv2.RANSAC,
                ransacReprojThreshold=self.reprojection_threshold,
                maxIters=self.max_iters,
                confidence=self.confidence,
            )
        except Exception:
            return self._build_safe_response(
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                input_matches_count=input_matches_count,
                status="RANSAC_FAILED",
            )

        if H is None or mask is None:
            return self._build_safe_response(
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                input_matches_count=input_matches_count,
                status="RANSAC_FAILED",
            )

        # Flatten mask to 1D uint8 array (1 for inliers, 0 for outliers)
        inlier_mask_1d = mask.ravel().astype(np.uint8)
        if len(inlier_mask_1d) != input_matches_count:
            return self._build_safe_response(
                tile_a_id=tile_a_id,
                tile_b_id=tile_b_id,
                input_matches_count=input_matches_count,
                status="RANSAC_FAILED",
            )

        bool_mask = inlier_mask_1d == 1
        inlier_count = int(np.sum(bool_mask))
        outlier_count = input_matches_count - inlier_count
        inlier_ratio = float(inlier_count / input_matches_count) if input_matches_count > 0 else 0.0

        src_inliers = clean_src[bool_mask].reshape(-1, 2)
        dst_inliers = clean_dst[bool_mask].reshape(-1, 2)

        status = "SUCCESS" if inlier_count > 0 else "RANSAC_FAILED"

        return {
            "homography": H.astype(np.float64) if H.shape == (3, 3) else H,
            "inlier_mask": inlier_mask_1d,
            "inlier_count": inlier_count,
            "outlier_count": outlier_count,
            "inlier_ratio": inlier_ratio,
            "src_inliers": src_inliers,
            "dst_inliers": dst_inliers,
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "input_matches_count": input_matches_count,
            "status": status,
        }

    def estimate(self, match_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary interface accepting the B6 FeatureMatcher result dictionary.

        Parameters
        ----------
        match_result : dict
            B6 FeatureMatcher output dictionary containing 'src_pts', 'dst_pts', 'tile_a_id', 'tile_b_id'.

        Returns
        -------
        dict
            Standardized RANSAC result dictionary.
        """
        if not isinstance(match_result, dict):
            return self._build_safe_response(
                tile_a_id=None,
                tile_b_id=None,
                input_matches_count=0,
                status="INVALID_INPUT",
            )

        src_pts = match_result.get("src_pts")
        dst_pts = match_result.get("dst_pts")
        tile_a_id = match_result.get("tile_a_id")
        tile_b_id = match_result.get("tile_b_id")

        return self.estimate_from_points(
            src_pts=src_pts,
            dst_pts=dst_pts,
            tile_a_id=tile_a_id,
            tile_b_id=tile_b_id,
        )

    def _build_safe_response(
        self,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
        input_matches_count: int = 0,
        status: str = "INSUFFICIENT_MATCHES",
    ) -> Dict[str, Any]:
        """Helper to construct safe failure / zero-inlier response."""
        return {
            "homography": None,
            "inlier_mask": np.empty((input_matches_count,), dtype=np.uint8),
            "inlier_count": 0,
            "outlier_count": input_matches_count,
            "inlier_ratio": 0.0,
            "src_inliers": np.empty((0, 2), dtype=np.float32),
            "dst_inliers": np.empty((0, 2), dtype=np.float32),
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "input_matches_count": input_matches_count,
            "status": status,
        }
