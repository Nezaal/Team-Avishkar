"""Lazy-loaded pretrained LoFTR and independently testable geometry estimation."""
from copy import deepcopy
import hashlib
import logging
from pathlib import Path

import cv2
import numpy as np

from .geometry import transform_points

LOG = logging.getLogger(__name__)
WEIGHTS_URL = "https://cmp.felk.cvut.cz/~mishkdmy/models/loftr_outdoor.ckpt"


class LoFTRMatcher:
    def __init__(self, device="auto", checkpoint=None, threads=4):
        import torch
        from kornia.feature import LoFTR
        from kornia.feature.loftr.loftr import default_cfg
        torch.set_num_threads(threads)
        self.device = "cuda" if device == "auto" and torch.cuda.is_available() else ("cpu" if device == "auto" else device)
        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable; install CUDA-enabled PyTorch on the H200")
        if checkpoint is None:
            cache = Path(torch.hub.get_dir()) / "checkpoints"
            cache.mkdir(parents=True, exist_ok=True)
            checkpoint = cache / "loftr_outdoor.ckpt"
            if not checkpoint.exists():
                temporary = cache / "loftr_outdoor.ckpt.part"
                LOG.info("Downloading pretrained outdoor LoFTR weights")
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                torch.hub.download_url_to_file(WEIGHTS_URL, str(temporary))
                temporary.replace(checkpoint)
        checkpoint = Path(checkpoint)
        self.checkpoint_sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        weights = torch.load(checkpoint, map_location="cpu", weights_only=True)
        self.model = LoFTR(pretrained=None, config=deepcopy(default_cfg))
        self.model.load_state_dict(weights.get("state_dict", weights), strict=True)
        self.model = self.model.eval().to(self.device)

    def __call__(self, source, reference, source_mask, reference_mask):
        import torch
        def padded(image, mask):
            h, w = image.shape
            ph, pw = (h + 7) // 8 * 8, (w + 7) // 8 * 8
            a = np.pad(image, ((0, ph-h), (0, pw-w)))
            m = np.pad(mask > 0, ((0, ph-h), (0, pw-w)))
            return torch.from_numpy(a).float()[None, None].to(self.device) / 255, torch.from_numpy(m).float()[None].to(self.device)
        a, ma = padded(source, source_mask)
        b, mb = padded(reference, reference_mask)
        with torch.inference_mode():
            pred = self.model({"image0": a, "image1": b, "mask0": ma, "mask1": mb})
        return tuple(pred[key].cpu().numpy() for key in ("keypoints0", "keypoints1", "confidence"))


def filter_matches(source, reference, scores, source_mask, reference_mask, threshold):
    valid = np.isfinite(source).all(1) & np.isfinite(reference).all(1) & np.isfinite(scores) & (scores >= threshold)
    # Remove fine-level matches in padding or invalid source pixels too.
    for points, mask in ((source, source_mask), (reference, reference_mask)):
        rounded = np.rint(np.nan_to_num(points)).astype(np.int64)
        inside = (points[:, 0] >= 0) & (points[:, 0] < mask.shape[1]) & (points[:, 1] >= 0) & (points[:, 1] < mask.shape[0])
        xx = rounded[:, 0].clip(0, mask.shape[1]-1)
        yy = rounded[:, 1].clip(0, mask.shape[0]-1)
        valid &= inside & (mask[yy, xx] > 0)
    return source[valid], reference[valid], scores[valid]


def hull_coverage(points, area):
    if len(points) < 3 or area <= 0:
        return 0.
    return float(min(1., cv2.contourArea(cv2.convexHull(np.asarray(points, np.float32))) / area))


def estimate(source, target, model="affine", threshold=2., seed=42):
    """Source working pixels -> native reference ROI pixels; threshold has native units."""
    if len(source) < 8:
        return None, np.zeros(len(source), bool), "Fewer than eight filtered correspondences"
    cv2.setRNGSeed(seed)
    if model == "affine":
        affine, mask = cv2.estimateAffine2D(np.asarray(source, np.float32), np.asarray(target, np.float32),
                                          method=cv2.RANSAC, ransacReprojThreshold=threshold,
                                          maxIters=5000, confidence=.999, refineIters=20)
        matrix = np.vstack([affine, [0., 0., 1.]]) if affine is not None else None
    elif model == "homography":
        matrix, mask = cv2.findHomography(np.asarray(source, np.float32), np.asarray(target, np.float32),
                                          cv2.USAC_MAGSAC, threshold, maxIters=5000, confidence=.999)
    else:
        raise ValueError("model must be affine or homography")
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        return None, np.zeros(len(source), bool), "Robust estimation failed"
    if abs(np.linalg.det(matrix)) < 1e-10:
        return None, np.zeros(len(source), bool), "Degenerate transformation"
    errors = np.linalg.norm(transform_points(matrix, source) - target, axis=1)
    inliers = mask.ravel().astype(bool) & (errors <= threshold)
    if inliers.sum() < 8:
        return None, inliers, "Fewer than eight geometrically consistent correspondences"
    return matrix, inliers, None


def residual_metrics(matrix, source, target, inliers):
    errors = np.linalg.norm(transform_points(matrix, source) - target, axis=1)
    e = errors[inliers]
    return errors, {"inlier_rmse_tmc2_px": float(np.sqrt(np.mean(e ** 2))),
                    "inlier_median_tmc2_px": float(np.median(e)),
                    "inlier_p95_tmc2_px": float(np.percentile(e, 95)),
                    "inlier_max_tmc2_px": float(e.max())}
