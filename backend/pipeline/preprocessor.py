"""
ChandraMatch Preprocessing Module (Module B4)

This module handles image preprocessing prior to SIFT feature extraction,
including grayscale conversion, intensity normalization, NoData mask generation,
working-resolution resizing, CLAHE contrast enhancement, and scale transformation metadata calculation.

Current Status: Step 14 — Grayscale conversion, percentile-based intensity normalization,
valid-pixel mask generation, configurable spatial resizing, and optional CLAHE implemented.
"""
import numpy as np

# Optional import of cv2 if available in the environment
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def preprocess_image(
    image_data: dict,
    working_scale: float = 1.0,
    clahe_clip: float = 2.0,
    apply_clahe: bool = False,
    apply_blur: bool = False
) -> dict:
    """
    Preprocess an image for downstream SIFT feature extraction.

    Implemented:
    - Step 10: Grayscale conversion (2D/3D inputs to 2D single channel)
    - Step 11: Percentile-based intensity normalization (maps valid pixels to 2D uint8)
    - Step 12: Valid-pixel mask generation (255 = valid, 0 = invalid / NoData)
    - Step 13: Configurable spatial resizing & coordinate scale tracking
    - Step 14: Optional CLAHE local contrast enhancement

    Parameters
    ----------
    image_data : dict
        Image container dictionary from Loader (Module B2) containing at minimum:
        - "array" : np.ndarray
        - "width" : int
        - "height" : int
        - "metadata" : dict (optional, may contain explicit NoData values)
    working_scale : float, optional
        Multiplicative dimension downsampling scale factor (> 0.0), default 1.0.
    clahe_clip : float, optional
        CLAHE contrast limit parameter (> 0.0), default 2.0.
    apply_clahe : bool, optional
        Whether to apply CLAHE contrast enhancement, default False.
    apply_blur : bool, optional
        Whether to apply light Gaussian noise reduction, default False.

    Returns
    -------
    dict
        Preprocessed image dictionary matching API Contract schema:
        - "image" : np.ndarray (2D uint8, working resolution)
        - "mask" : np.ndarray (2D uint8, working resolution, 255=valid, 0=invalid)
        - "scale_x" : float (original_width / working_width)
        - "scale_y" : float (original_height / working_height)
        - "original_width" : int
        - "original_height" : int
        - "working_width" : int
        - "working_height" : int
        - "operations" : list[str]
        - "parameters" : dict

    Raises
    ------
    TypeError
        If image_data is not a dictionary or array is not a numpy ndarray.
    ValueError
        If array is missing, dimensions <= 0, parameter values <= 0, array dimension
        is unsupported, channel count is unsupported, metadata dimensions mismatch,
        or no valid finite pixels exist for normalization.
    """
    if not isinstance(image_data, dict):
        raise TypeError("image_data must be a dictionary.")

    if "array" not in image_data:
        raise ValueError("image_data must contain 'array' key.")

    raw_array = image_data["array"]
    if not isinstance(raw_array, np.ndarray):
        raise TypeError("image_data['array'] must be a numpy ndarray.")

    width = image_data.get("width")
    if width is None or not isinstance(width, (int, float)) or width <= 0:
        raise ValueError("image_data['width'] must be a positive number.")
    width = int(width)

    height = image_data.get("height")
    if height is None or not isinstance(height, (int, float)) or height <= 0:
        raise ValueError("image_data['height'] must be a positive number.")
    height = int(height)

    if not isinstance(working_scale, (int, float)) or working_scale <= 0:
        raise ValueError("working_scale must be a positive float.")

    if not isinstance(clahe_clip, (int, float)) or clahe_clip <= 0:
        raise ValueError("clahe_clip must be a positive float.")

    # --- Step 10: Grayscale Conversion ---
    ndim = raw_array.ndim
    if ndim == 2:
        gray_array = raw_array
    elif ndim == 3:
        channels = raw_array.shape[2]
        if channels == 1:
            gray_array = raw_array[:, :, 0]
        elif channels in (3, 4):
            if _HAS_CV2:
                code = cv2.COLOR_BGR2GRAY if channels == 3 else cv2.COLOR_BGRA2GRAY
                gray_array = cv2.cvtColor(raw_array, code)
            else:
                bgr_weights = np.array([0.114, 0.587, 0.299], dtype=np.float32)
                gray_array = np.dot(raw_array[:, :, :3].astype(np.float32), bgr_weights).astype(raw_array.dtype)
        else:
            raise ValueError(
                f"Unsupported channel count {channels} for 3D array. "
                "Expected 1, 3, or 4 channels."
            )
    else:
        raise ValueError(
            f"Unsupported array dimension {ndim}D. "
            "Expected 2D (H, W) or 3D (H, W, C) image array."
        )

    # Verify spatial dimensions against metadata
    actual_height, actual_width = gray_array.shape[:2]
    if actual_width != width or actual_height != height:
        raise ValueError(
            f"Image array shape ({actual_height}, {actual_width}) does not match "
            f"metadata dimensions ({height}, {width})."
        )

    # --- Step 12: NoData / Valid-Pixel Mask Detection ---
    nodata_val = None
    metadata_dict = image_data.get("metadata")
    if isinstance(metadata_dict, dict):
        for key in ("nodata", "no_data", "NoData", "NODATA", "nodata_value"):
            if key in metadata_dict and metadata_dict[key] is not None:
                nodata_val = metadata_dict[key]
                break

    is_float = np.issubdtype(gray_array.dtype, np.floating)
    if is_float:
        valid_bool = np.isfinite(gray_array)
        if nodata_val is not None:
            valid_bool = valid_bool & (gray_array != nodata_val)
    else:
        if nodata_val is not None:
            valid_bool = (gray_array != nodata_val)
        else:
            valid_bool = np.ones(gray_array.shape, dtype=bool)

    valid_mask = np.where(valid_bool, np.uint8(255), np.uint8(0)).astype(np.uint8)
    valid_mask = np.ascontiguousarray(valid_mask)

    # --- Step 11: Percentile-Based Intensity Normalization (Mask-Aware) ---
    valid_pixels = gray_array[valid_bool]

    if valid_pixels.size == 0:
        raise ValueError("No valid finite pixels found for intensity normalization.")

    lower_p = 1.0
    upper_p = 99.0
    low = float(np.percentile(valid_pixels, lower_p))
    high = float(np.percentile(valid_pixels, upper_p))

    if high < low:
        raise ValueError(f"Invalid percentile bounds: low ({low}) > high ({high}).")

    if low == high:
        norm_uint8 = np.full(gray_array.shape, 128, dtype=np.uint8)
    else:
        clipped = np.clip(gray_array, low, high)
        normalized = (clipped - low) / (high - low) * 255.0
        normalized = np.where(valid_bool, normalized, 0.0)
        norm_uint8 = np.clip(normalized, 0, 255).astype(np.uint8)

    norm_uint8 = np.where(valid_bool, norm_uint8, np.uint8(0))
    norm_uint8 = np.ascontiguousarray(norm_uint8)

    # --- Step 13: Configurable Spatial Resizing ---
    working_width = max(1, int(round(width * working_scale)))
    working_height = max(1, int(round(height * working_scale)))

    if working_width == width and working_height == height:
        resized_image = norm_uint8
        resized_mask = valid_mask
        interp_name = "none"
    else:
        if _HAS_CV2:
            if working_scale < 1.0:
                interp_img = cv2.INTER_AREA
                interp_name = "cv2.INTER_AREA"
            else:
                interp_img = cv2.INTER_LINEAR
                interp_name = "cv2.INTER_LINEAR"

            resized_image = cv2.resize(norm_uint8, (working_width, working_height), interpolation=interp_img)
            resized_mask = cv2.resize(valid_mask, (working_width, working_height), interpolation=cv2.INTER_NEAREST)
        else:
            y_indices = np.linspace(0, height - 1, working_height).astype(int)
            x_indices = np.linspace(0, width - 1, working_width).astype(int)
            resized_image = norm_uint8[np.ix_(y_indices, x_indices)]
            resized_mask = valid_mask[np.ix_(y_indices, x_indices)]
            interp_name = "numpy_grid_sampling"

    resized_image = np.ascontiguousarray(resized_image, dtype=np.uint8)
    resized_mask = np.ascontiguousarray(resized_mask, dtype=np.uint8)

    # --- Step 14: Optional CLAHE Contrast Enhancement ---
    operations = ["grayscale", "contrast_normalization"]
    if working_scale != 1.0:
        operations.append("resize")

    if apply_clahe:
        if _HAS_CV2:
            clahe = cv2.createCLAHE(clipLimit=float(clahe_clip), tileGridSize=(8, 8))
            clahe_image = clahe.apply(resized_image)
        else:
            clahe_image = resized_image

        resized_image = np.where(resized_mask > 0, clahe_image, np.uint8(0))
        resized_image = np.ascontiguousarray(resized_image, dtype=np.uint8)
        operations.append("clahe")
        clahe_applied = True
    else:
        clahe_applied = False

    scale_x = float(width) / float(working_width)
    scale_y = float(height) / float(working_height)

    valid_count = int(np.count_nonzero(resized_mask > 0))
    total_count = int(resized_mask.size)

    return {
        "image": resized_image,
        "mask": resized_mask,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "original_width": width,
        "original_height": height,
        "working_width": working_width,
        "working_height": working_height,
        "operations": operations,
        "parameters": {
            "working_scale": float(working_scale),
            "clahe_clip": float(clahe_clip),
            "clahe_applied": clahe_applied,
            "clahe_tile_grid": [8, 8],
            "scale_x": scale_x,
            "scale_y": scale_y,
            "interpolation": interp_name,
            "normalization_method": "percentile",
            "lower_percentile": lower_p,
            "upper_percentile": upper_p,
            "lower_value": low,
            "upper_value": high,
            "nodata_present": nodata_val is not None,
            "nodata_value": nodata_val,
            "valid_pixel_count": valid_count,
            "invalid_pixel_count": total_count - valid_count,
        },
    }
