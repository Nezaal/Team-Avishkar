"""
ChandraMatch SIFT Feature Extractor (Module B5)

Extracts SIFT keypoints and 128-dimensional float32 descriptors from 512x512
preprocessed lunar tile images and validity masks. Supports both NumPy arrays and
PyTorch Tensors, handling zero-keypoint edge cases safely.

Usage:
    extractor = SiftFeatureExtractor()
    features = extractor.extract_from_sample(sample)
    # Returns {"keypoints": [...], "descriptors": ndarray(N, 128), "count": N, "tile_id": str}
"""
from typing import Dict, Any, Optional, Union, List, Tuple
import numpy as np
import cv2

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class SiftFeatureExtractor:
    """
    Mask-aware SIFT feature extractor for preprocessed lunar tile images.
    """

    def __init__(
        self,
        nfeatures: int = 0,
        contrast_threshold: float = 0.04,
        edge_threshold: float = 10.0,
        sigma: float = 1.6,
    ):
        """
        Parameters
        ----------
        nfeatures : int, optional
            Number of best features to retain (0 = all detected). Default is 0.
        contrast_threshold : float, optional
            The contrast threshold used to filter weak features in low-contrast regions. Default 0.04.
        edge_threshold : float, optional
            The threshold used to filter out edge-like features. Default 10.0.
        sigma : float, optional
            The sigma of the Gaussian applied to the input image at octave #0. Default 1.6.
        """
        self.nfeatures = int(nfeatures)
        self.contrast_threshold = float(contrast_threshold)
        self.edge_threshold = float(edge_threshold)
        self.sigma = float(sigma)

        # Create internal OpenCV SIFT instance
        self.sift = cv2.SIFT_create(
            nfeatures=self.nfeatures,
            contrastThreshold=self.contrast_threshold,
            edgeThreshold=self.edge_threshold,
            sigma=self.sigma,
        )

    def _to_numpy_uint8(
        self, arr: Union[np.ndarray, Any], name: str = "image"
    ) -> np.ndarray:
        """Helper to convert input (NumPy array or PyTorch Tensor) to a 2D uint8 NumPy array."""
        if arr is None:
            raise ValueError(f"{name} cannot be None")

        # Convert PyTorch tensor to numpy if applicable
        if HAS_TORCH and isinstance(arr, torch.Tensor):
            arr = arr.detach().cpu().numpy()

        if not isinstance(arr, np.ndarray):
            raise TypeError(f"{name} must be a NumPy ndarray or PyTorch Tensor, got {type(arr)}")

        if arr.ndim != 2:
            # Squeeze single-channel dimensions if 3D (e.g., (1, H, W) or (H, W, 1))
            if arr.ndim == 3 and (arr.shape[0] == 1 or arr.shape[2] == 1):
                arr = arr.squeeze()
            else:
                raise ValueError(f"{name} must be 2-dimensional, got shape {arr.shape}")

        if arr.dtype != np.uint8:
            # Convert dtype safely
            if np.issubdtype(arr.dtype, np.floating):
                if arr.max() <= 1.0 and arr.min() >= 0.0:
                    arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    arr = np.clip(arr, 0, 255).astype(np.uint8)
            else:
                arr = arr.astype(np.uint8)

        return arr

    def extract(
        self,
        image: Union[np.ndarray, Any],
        mask: Optional[Union[np.ndarray, Any]] = None,
        tile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract SIFT keypoints and descriptors from a 2D image array or tensor.

        Parameters
        ----------
        image : np.ndarray or torch.Tensor
            2D grayscale image (uint8, e.g. 512x512).
        mask : np.ndarray or torch.Tensor, optional
            2D binary validity mask (uint8, 255=valid, 0=invalid).
        tile_id : str, optional
            Identifier string for the tile.

        Returns
        -------
        dict
            {
                "keypoints": list[cv2.KeyPoint],
                "descriptors": np.ndarray (N, 128) float32,
                "count": int,
                "tile_id": str or None
            }
        """
        img_np = self._to_numpy_uint8(image, name="image")

        mask_np = None
        if mask is not None:
            mask_np = self._to_numpy_uint8(mask, name="mask")
            if mask_np.shape != img_np.shape:
                raise ValueError(
                    f"Mask shape {mask_np.shape} does not match image shape {img_np.shape}"
                )

        # Detect SIFT keypoints & compute descriptors with optional mask
        keypoints, descriptors = self.sift.detectAndCompute(img_np, mask_np)

        # Handle zero-keypoint and empty descriptor cases safely
        if keypoints is None:
            keypoints = []

        if descriptors is None or len(keypoints) == 0:
            descriptors_out = np.empty((0, 128), dtype=np.float32)
            count = 0
            keypoints_out = []
        else:
            descriptors_out = np.asarray(descriptors, dtype=np.float32)
            count = len(keypoints)
            keypoints_out = list(keypoints)

        return {
            "keypoints": keypoints_out,
            "descriptors": descriptors_out,
            "count": count,
            "tile_id": tile_id,
        }

    def extract_from_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract SIFT features directly from an OHRCTileDataset sample dictionary.

        Parameters
        ----------
        sample : dict
            Sample dictionary from OHRCTileDataset containing 'preprocessed', 'mask', and 'tile_id'.

        Returns
        -------
        dict
            Feature extraction result dictionary matching the extract() contract.
        """
        if not isinstance(sample, dict):
            raise TypeError(f"Sample must be a dictionary, got {type(sample)}")

        if "preprocessed" not in sample:
            raise KeyError("Sample dictionary missing required 'preprocessed' key")

        prep_img = sample["preprocessed"]
        mask = sample.get("mask")
        tile_id = sample.get("tile_id")

        return self.extract(image=prep_img, mask=mask, tile_id=tile_id)
