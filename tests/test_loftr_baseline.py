import json
from pathlib import Path

import cv2
import numpy as np

from loftr_pipeline.geometry import resize_matrix, transform_points
from loftr_pipeline.matching import estimate
from loftr_pipeline.pipeline import RunConfig, run


def test_resize_coordinate_convention():
    matrix = resize_matrix(10, 10, 20, 20)
    assert np.allclose(transform_points(matrix, [[0, 0], [9, 9]]), [[.5, .5], [18.5, 18.5]])


def test_affine_robust_estimation_rejects_outliers():
    rng = np.random.default_rng(7)
    source = rng.uniform(0, 200, (80, 2))
    truth = np.array([[1.04, -.03, 14], [.04, .98, -7], [0, 0, 1.]])
    target = transform_points(truth, source) + rng.normal(0, .15, source.shape)
    target[:12] = rng.uniform(-500, 500, (12, 2))
    matrix, inliers, reason = estimate(source, target, "affine", 1.)
    assert reason is None and inliers.sum() >= 65
    assert np.sqrt(np.mean(np.sum((transform_points(matrix, source[inliers]) - transform_points(truth, source[inliers])) ** 2, 1))) < .5


class FakeStore:
    def __init__(self):
        self.repo_id, self.revision = "test/repo", "deadbeef"
        self.products = {"o": {"width": 512, "height": 512}, "t": {"width": 512, "height": 512}}
    def pair(self, _):
        return {"pair_id": "pair_test", "ohrc_product_id": "o", "tmc2_product_id": "t", "ohrc_resolution_m": "1", "tmc2_resolution_m": "1"}
    def assemble(self, product_id, roi, workers):
        image = np.tile(np.linspace(20, 180, roi[2], dtype=np.float32), (roi[3], 1))
        for i in range(30, min(roi[2], roi[3]), 40): cv2.circle(image, (i, i), 7, 230, -1)
        return image, np.full(image.shape, 255, np.uint8)


class FakeMatcher:
    device, checkpoint_sha256 = "cpu", "test"
    def __call__(self, source, reference, source_mask, reference_mask):
        xx, yy = np.meshgrid(np.arange(60., 261., 40.), np.arange(60., 261., 40.))
        points = np.c_[xx.ravel(), yy.ravel()]
        return points, points + np.array([2., -3.]), np.full(len(points), .95)


def test_pipeline_exports_evidence(tmp_path):
    config = RunConfig(pair_id="pair_test", source_roi=[0, 0, 512, 512], reference_roi=[0, 0, 512, 512],
                       max_size=512, output_root=str(tmp_path), min_confidence=.1, ransac_threshold=1.)
    result = run(config, matcher=FakeMatcher(), store=FakeStore(), run_id="a" * 32)
    path = tmp_path / ("a" * 32)
    assert result["status"] == "REGISTERED_UNVERIFIED"
    assert (path / "result.json").is_file() and (path / "matches.png").is_file() and (path / "overlay.png").is_file()
    assert len(json.loads((path / "result.json").read_text())["correspondences"]) == 36
