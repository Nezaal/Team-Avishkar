"""
ChandraMatch Image Registration & Warping (Module B8)

Warps moving lunar image tiles into the coordinate system of reference tiles using
the homography matrix estimated by Module B7 (RansacEstimator). Evaluates registration
quality metrics (MAE, MSE, RMSE, valid pixel ratio) strictly over mutually valid pixel regions.
"""
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import cv2


class ImageRegistration:
    """
    Image registration and warping engine for preprocessed lunar tile images.
    """

    def __init__(
        self,
        interpolation: int = cv2.INTER_LINEAR,
        border_mode: int = cv2.BORDER_CONSTANT,
        border_value: int = 0,
    ):
        """
        Parameters
        ----------
        interpolation : int, optional
            OpenCV interpolation flag for image warping (default cv2.INTER_LINEAR).
        border_mode : int, optional
            OpenCV border mode for out-of-bounds pixels (default cv2.BORDER_CONSTANT).
        border_value : int, optional
            Constant pixel value for out-of-bounds border regions (default 0).
        """
        self.interpolation = int(interpolation)
        self.border_mode = int(border_mode)
        self.border_value = int(border_value)

    def validate_image(self, img: Any, name: str = "image") -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Validate and normalize input image array.

        Returns
        -------
        (is_valid, clean_np_array, status_code)
        """
        if img is None:
            return False, None, "INVALID_INPUT"

        if not isinstance(img, np.ndarray):
            try:
                img = np.asarray(img)
            except Exception:
                return False, None, "INVALID_INPUT"

        if img.size == 0 or img.ndim != 2:
            # Handle single-channel 3D if squeezeable (e.g. (1, H, W) or (H, W, 1))
            if img.ndim == 3 and (img.shape[0] == 1 or img.shape[2] == 1):
                img = img.squeeze()
            else:
                return False, None, "INVALID_INPUT"

        if img.shape[0] < 1 or img.shape[1] < 1:
            return False, None, "INVALID_INPUT"

        if not np.issubdtype(img.dtype, np.number):
            return False, None, "INVALID_INPUT"

        return True, img, "SUCCESS"

    def validate_homography(self, H: Any) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Validate 3x3 homography matrix.
        """
        if H is None:
            return False, None, "INVALID_HOMOGRAPHY"

        if not isinstance(H, np.ndarray):
            try:
                H = np.asarray(H)
            except Exception:
                return False, None, "INVALID_HOMOGRAPHY"

        if H.shape != (3, 3):
            return False, None, "INVALID_HOMOGRAPHY"

        if np.isnan(H).any() or np.isinf(H).any():
            return False, None, "INVALID_HOMOGRAPHY"

        return True, H.astype(np.float64), "SUCCESS"

    def register(
        self,
        image_a: Any,
        image_b: Any,
        ransac_result: Dict[str, Any],
        mask_a: Optional[Any] = None,
        mask_b: Optional[Any] = None,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register moving image (image_b) into the coordinate system of reference image (image_a).

        Parameters
        ----------
        image_a : np.ndarray
            Reference image (Tile A, 2D uint8 or float32).
        image_b : np.ndarray
            Moving image (Tile B, 2D uint8 or float32).
        ransac_result : dict
            B7 RansacEstimator output dictionary containing 'homography' and 'status'.
        mask_a : np.ndarray, optional
            Reference validity mask (uint8, 255=valid, 0=invalid).
        mask_b : np.ndarray, optional
            Moving validity mask (uint8, 255=valid, 0=invalid).
        tile_a_id : str, optional
            Identifier for Tile A.
        tile_b_id : str, optional
            Identifier for Tile B.

        Returns
        -------
        dict
            Standardized registration result dictionary.
        """
        # Extract tile IDs from ransac_result if not provided explicitly
        if tile_a_id is None and isinstance(ransac_result, dict):
            tile_a_id = ransac_result.get("tile_a_id")
        if tile_b_id is None and isinstance(ransac_result, dict):
            tile_b_id = ransac_result.get("tile_b_id")

        # Validate reference and moving images
        valid_ref, ref_img, status_ref = self.validate_image(image_a, "reference")
        if not valid_ref:
            return self._build_safe_response(tile_a_id, tile_b_id, status=status_ref)

        valid_mov, mov_img, status_mov = self.validate_image(image_b, "moving")
        if not valid_mov:
            return self._build_safe_response(
                tile_a_id, tile_b_id, reference_shape=ref_img.shape if ref_img is not None else None, status=status_mov
            )

        # Enforce shape compatibility
        if ref_img.shape != mov_img.shape:
            return self._build_safe_response(
                tile_a_id, tile_b_id, reference_shape=ref_img.shape, status="INVALID_INPUT"
            )

        # Validate RANSAC result status & homography
        if not isinstance(ransac_result, dict) or ransac_result.get("status") != "SUCCESS":
            return self._build_safe_response(
                tile_a_id, tile_b_id, reference_shape=ref_img.shape, status="INVALID_HOMOGRAPHY"
            )

        raw_H = ransac_result.get("homography")
        valid_H, H, status_H = self.validate_homography(raw_H)
        if not valid_H:
            return self._build_safe_response(
                tile_a_id, tile_b_id, reference_shape=ref_img.shape, status=status_H
            )

        ref_h, ref_w = ref_img.shape
        dsize = (ref_w, ref_h)

        # Execute warpPerspective on moving image
        try:
            registered_img = cv2.warpPerspective(
                mov_img,
                H,
                dsize,
                flags=self.interpolation,
                borderMode=self.border_mode,
                borderValue=self.border_value,
            )
        except Exception:
            return self._build_safe_response(
                tile_a_id, tile_b_id, reference_shape=ref_img.shape, status="REGISTRATION_FAILED"
            )

        # Process validity masks if provided
        registered_mask = None
        ref_valid_mask = np.ones(ref_img.shape, dtype=bool)

        if mask_a is not None:
            valid_m_a, clean_m_a, _ = self.validate_image(mask_a, "mask_a")
            if valid_m_a and clean_m_a.shape == ref_img.shape:
                ref_valid_mask = clean_m_a == 255

        mov_valid_mask = np.ones(ref_img.shape, dtype=bool)
        if mask_b is not None:
            valid_m_b, clean_m_b, _ = self.validate_image(mask_b, "mask_b")
            if valid_m_b and clean_m_b.shape == mov_img.shape:
                try:
                    registered_mask = cv2.warpPerspective(
                        clean_m_b,
                        H,
                        dsize,
                        flags=cv2.INTER_NEAREST,
                        borderMode=cv2.BORDER_CONSTANT,
                        borderValue=0,
                    )
                    # Enforce strict binary uint8 (0 or 255)
                    registered_mask = np.where(registered_mask >= 128, np.uint8(255), np.uint8(0))
                    mov_valid_mask = registered_mask == 255
                except Exception:
                    registered_mask = None

        # Compute mutually valid pixel mask
        mutually_valid = ref_valid_mask & mov_valid_mask
        valid_pixel_count = int(np.sum(mutually_valid))
        total_pixels = ref_img.size
        valid_pixel_ratio = float(valid_pixel_count / total_pixels) if total_pixels > 0 else 0.0

        if valid_pixel_count == 0:
            return {
                "registered_image": registered_img,
                "registered_mask": registered_mask,
                "homography": H,
                "metrics": {
                    "mae": None,
                    "mse": None,
                    "rmse": None,
                    "valid_pixel_count": 0,
                    "valid_pixel_ratio": 0.0,
                },
                "tile_a_id": tile_a_id,
                "tile_b_id": tile_b_id,
                "reference_shape": ref_img.shape,
                "status": "EMPTY_VALID_REGION",
            }

        # Calculate MAE, MSE, RMSE on mutually valid pixels strictly
        diff = ref_img[mutually_valid].astype(np.float32) - registered_img[mutually_valid].astype(np.float32)
        mae = float(np.mean(np.abs(diff)))
        mse = float(np.mean(diff ** 2))
        rmse = float(np.sqrt(mse))

        return {
            "registered_image": registered_img,
            "registered_mask": registered_mask,
            "homography": H,
            "metrics": {
                "mae": mae,
                "mse": mse,
                "rmse": rmse,
                "valid_pixel_count": valid_pixel_count,
                "valid_pixel_ratio": valid_pixel_ratio,
            },
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "reference_shape": ref_img.shape,
            "status": "SUCCESS",
        }

    def _build_safe_response(
        self,
        tile_a_id: Optional[str] = None,
        tile_b_id: Optional[str] = None,
        reference_shape: Optional[Tuple[int, int]] = None,
        status: str = "REGISTRATION_FAILED",
    ) -> Dict[str, Any]:
        """Helper to construct safe failure response."""
        return {
            "registered_image": None,
            "registered_mask": None,
            "homography": None,
            "metrics": {
                "mae": None,
                "mse": None,
                "rmse": None,
                "valid_pixel_count": 0,
                "valid_pixel_ratio": 0.0,
            },
            "tile_a_id": tile_a_id,
            "tile_b_id": tile_b_id,
            "reference_shape": reference_shape,
            "status": status,
        }
