"""
ChandraMatch Pair Analyzer (Module B3)

Analyzes an OHRC/TMC-2 image pair to determine optimal preprocessing
parameters. Computes resolution ratio, contrast metrics, texture scores,
and recommends working_scale + CLAHE settings for each image.

Usage:
    analyzer = PairAnalyzer()
    result = analyzer.analyze(ohrc_image, tmc2_image)
"""
import numpy as np


# Target shorter dimension for SIFT (pixels)
TARGET_SHORT_DIM = 3000

# Minimum acceptable shorter dimension
MIN_SHORT_DIM = 1000


def compute_contrast(image_array, sample_size=100000):
    """Compute contrast as std dev of pixel values (sampled for speed)."""
    flat = image_array.ravel()
    if len(flat) > sample_size:
        idx = np.random.default_rng(42).choice(len(flat), sample_size, replace=False)
        flat = flat[idx]
    return float(np.std(flat))


def compute_texture_score(image_array, sample_size=200000):
    """
    Compute texture score using variance of Laplacian.
    Higher = more textured (better for SIFT).
    Sampled for speed on large images.
    """
    h, w = image_array.shape[:2]

    # For very large images, downsample first
    if h * w > sample_size * 4:
        scale = min(1.0, np.sqrt(sample_size * 4 / (h * w)))
        new_h = max(100, int(h * scale))
        new_w = max(100, int(w * scale))
        # Simple downsample via slicing
        step_h = max(1, h // new_h)
        step_w = max(1, w // new_w)
        small = image_array[::step_h, ::step_w].astype(np.float32)
    else:
        small = image_array.astype(np.float32)

    # Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)

    # Simple convolution via correlation (pad edges)
    padded = np.pad(small, 1, mode="edge")
    lap = np.zeros_like(small)
    for i in range(small.shape[0]):
        for j in range(small.shape[1]):
            lap[i, j] = np.sum(padded[i : i + 3, j : j + 3] * kernel)

    return float(np.var(lap))


def compute_texture_score_fast(image_array):
    """
    Fast texture score using pixel intensity variance in small patches.
    Much faster than Laplacian for large images.
    """
    h, w = image_array.shape[:2]
    # Sample 100x100 patches across the image
    patch_size = 100
    n_patches = min(50, (h // patch_size) * (w // patch_size))
    if n_patches == 0:
        return compute_contrast(image_array)

    rng = np.random.default_rng(42)
    max_h = h - patch_size
    max_w = w - patch_size
    if max_h <= 0 or max_w <= 0:
        return compute_contrast(image_array)

    vars_list = []
    for _ in range(n_patches):
        y = rng.integers(0, max_h)
        x = rng.integers(0, max_w)
        patch = image_array[y : y + patch_size, x : x + patch_size].astype(np.float32)
        vars_list.append(float(np.var(patch)))

    return float(np.mean(vars_list))


def recommend_working_scale(width, height, target_dim=TARGET_SHORT_DIM):
    """
    Recommend a working scale factor so the shorter dimension
    is approximately target_dim pixels.
    """
    short_dim = min(width, height)
    if short_dim <= 0:
        return 1.0
    scale = target_dim / short_dim
    # Clamp to reasonable range
    scale = max(0.05, min(1.0, scale))
    return round(scale, 4)


class PairAnalyzer:
    """Analyze an OHRC/TMC-2 pair and recommend preprocessing parameters."""

    def analyze(self, source, reference):
        """
        Analyze a pair of loaded images.

        Parameters
        ----------
        source : dict
            Loaded image dict from ImageLoader (OHRC).
        reference : dict
            Loaded image dict from ImageLoader (TMC-2).

        Returns
        -------
        dict
            Analysis results with recommended preprocessing parameters.
        """
        src_w = source["width"]
        src_h = source["height"]
        ref_w = reference["width"]
        ref_h = reference["height"]

        # Resolution ratio
        src_res = source["metadata"].get("pixel_resolution_m") or 0.25
        ref_res = reference["metadata"].get("pixel_resolution_m") or 5.0
        resolution_ratio = ref_res / src_res if src_res > 0 else 20.0

        # Working scale recommendations
        src_scale = recommend_working_scale(src_w, src_h)
        ref_scale = recommend_working_scale(ref_w, ref_h)

        # Contrast (sampled)
        src_contrast = compute_contrast(source["array"])
        ref_contrast = compute_contrast(reference["array"])

        # Texture (fast method)
        src_texture = compute_texture_score_fast(source["array"])
        ref_texture = compute_texture_score_fast(reference["array"])

        # CLAHE recommendation
        # Low contrast or low texture → recommend CLAHE
        src_low_contrast = src_contrast < 30.0
        src_low_texture = src_texture < 100.0
        recommend_clahe = src_low_contrast or src_low_texture

        # Working dimensions after scaling
        src_working_w = max(1, int(round(src_w * src_scale)))
        src_working_h = max(1, int(round(src_h * src_scale)))
        ref_working_w = max(1, int(round(ref_w * ref_scale)))
        ref_working_h = max(1, int(round(ref_h * ref_scale)))

        return {
            "resolution_ratio": round(resolution_ratio, 2),
            "source_resolution_m": src_res,
            "reference_resolution_m": ref_res,
            "source_working_scale": src_scale,
            "reference_working_scale": ref_scale,
            "source_working_dims": (src_working_w, src_working_h),
            "reference_working_dims": (ref_working_w, ref_working_h),
            "source_contrast": round(src_contrast, 2),
            "reference_contrast": round(ref_contrast, 2),
            "source_texture": round(src_texture, 2),
            "reference_texture": round(ref_texture, 2),
            "recommend_clahe": recommend_clahe,
            "clahe_clip": 2.0,
        }

    def print_report(self, result):
        """Print a human-readable analysis report."""
        print(f"\n{'=' * 50}")
        print(f"Pair Analysis Report")
        print(f"{'=' * 50}")
        print(f"Resolution ratio:      {result['resolution_ratio']:.1f}x")
        print(f"  Source resolution:   {result['source_resolution_m']} m/px")
        print(f"  Reference resolution:{result['reference_resolution_m']} m/px")
        print(f"\nWorking scales:")
        print(f"  Source:      {result['source_working_scale']:.4f} -> {result['source_working_dims'][0]}x{result['source_working_dims'][1]}")
        print(f"  Reference:   {result['reference_working_scale']:.4f} -> {result['reference_working_dims'][0]}x{result['reference_working_dims'][1]}")
        print(f"\nImage quality:")
        print(f"  Source contrast:     {result['source_contrast']:.1f}")
        print(f"  Reference contrast:  {result['reference_contrast']:.1f}")
        print(f"  Source texture:      {result['source_texture']:.1f}")
        print(f"  Reference texture:   {result['reference_texture']:.1f}")
        print(f"\nRecommendations:")
        print(f"  CLAHE:    {'YES' if result['recommend_clahe'] else 'NO'}")
        print(f"  CLAHE clip: {result['clahe_clip']}")
        print(f"{'=' * 50}")
