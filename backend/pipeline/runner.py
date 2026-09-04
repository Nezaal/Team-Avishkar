"""
ChandraMatch Pipeline Runner

Orchestrates the full preprocessing pipeline for an OHRC/TMC-2 pair:
1. Load pair metadata from pairs.csv
2. Load both images (memory-mapped)
3. Analyze pair characteristics
4. Crop TMC-2 to match OHRC along-track extent
5. Preprocess both images (grayscale, normalize, resize, CLAHE)

Usage:
    runner = PipelineRunner()
    result = runner.run("pair_001")
"""
import csv
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PAIRS_CSV = os.path.join(ROOT, "ground_truth", "manifests", "pairs.csv")

# Add backend to path for imports
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline.loader import ImageLoader
from pipeline.pair_analyzer import PairAnalyzer
from pipeline.preprocessor import preprocess_image


def load_pairs(pairs_csv=None):
    """Load pairs.csv and return list of dicts."""
    csv_path = pairs_csv or PAIRS_CSV
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
    """
    Crop the TMC-2 image along-track to match the OHRC's extent,
    centered on the TMC-2 strip.

    The TMC-2 strip is typically ~280k lines long while the OHRC is ~93k lines.
    We crop the TMC-2 to approximately match the OHRC's along-track coverage,
    scaled by the resolution ratio.

    Parameters
    ----------
    tmc2_array : np.ndarray
        The full TMC-2 image (memmap or array).
    ohrc_height : int
        OHRC along-track dimension (lines).
    ohrc_width : int
        OHRC across-track dimension (samples).
    tmc2_height : int
        TMC-2 along-track dimension (lines).
    tmc2_width : int
        TMC-2 across-track dimension (samples).

    Returns
    -------
    np.ndarray
        Cropped TMC-2 array (or full array if no cropping needed).
    """
    # The OHRC covers ~23km along-track at 0.25m/px
    # TMC-2 covers ~4.5m/px, so equivalent extent = ohrc_height * (0.25/4.5) lines
    ohrc_res = 0.25  # m/px, typical
    tmc2_res = 4.5   # m/px, typical
    resolution_ratio = ohrc_res / tmc2_res  # ~0.056

    # TMC-2 lines that correspond to OHRC's along-track extent
    tmc2_lines_needed = int(ohrc_height * resolution_ratio)
    # Add 50% margin for SIFT edge effects
    tmc2_lines_needed = int(tmc2_lines_needed * 1.5)
    # Clamp to actual image size
    tmc2_lines_needed = min(tmc2_lines_needed, tmc2_height)

    if tmc2_lines_needed >= tmc2_height:
        return tmc2_array  # No cropping needed

    # Center the crop on the TMC-2 strip
    start_line = (tmc2_height - tmc2_lines_needed) // 2
    end_line = start_line + tmc2_lines_needed

    print(f"  Cropping TMC-2: lines {start_line}-{end_line} ({tmc2_lines_needed} of {tmc2_height})")

    # For memmap, slicing returns a view — no data loaded until accessed
    return tmc2_array[start_line:end_line, :]


class PipelineRunner:
    """Run the preprocessing pipeline for OHRC/TMC-2 pairs."""

    def __init__(self, catalog_path=None, pairs_csv=None):
        self.loader = ImageLoader(catalog_path)
        self.analyzer = PairAnalyzer()
        self.pairs_csv = pairs_csv

    def run_preprocessing(self, pair_id, working_scale=None, apply_clahe=None, clahe_clip=2.0):
        """
        Run preprocessing pipeline for a single pair.

        Parameters
        ----------
        pair_id : str
            Pair ID (e.g. "pair_001").
        working_scale : float, optional
            Override working scale for source (OHRC). If None, uses analyzer recommendation.
        apply_clahe : bool, optional
            Override CLAHE setting. If None, uses analyzer recommendation.
        clahe_clip : float
            CLAHE clip limit.

        Returns
        -------
        dict
            {
                "pair_id": str,
                "analysis": dict,
                "source_preprocessed": dict,
                "reference_preprocessed": dict,
            }
        """
        pair = get_pair(pair_id, self.pairs_csv)
        ohrc_id = pair["ohrc_product_id"]
        tmc2_id = pair["tmc2_product_id"]

        print(f"\n{'=' * 60}")
        print(f"Running pipeline for {pair_id}")
        print(f"  Source (OHRC): {ohrc_id}")
        print(f"  Reference (TMC-2): {tmc2_id}")
        print(f"{'=' * 60}")

        # Step 1: Load images
        print("\n[1/4] Loading images...")
        source = self.loader.load(ohrc_id)
        reference = self.loader.load(tmc2_id)
        print(f"  OHRC: {source['width']}x{source['height']} {source['dtype']}")
        print(f"  TMC-2: {reference['width']}x{reference['height']} {reference['dtype']}")

        # Step 2: Analyze pair
        print("\n[2/4] Analyzing pair...")
        analysis = self.analyzer.analyze(source, reference)
        self.analyzer.print_report(analysis)

        # Step 3: Crop TMC-2 to OHRC extent
        print("\n[3/4] Cropping TMC-2 to OHRC extent...")
        ref_cropped = crop_tmc2_to_ohrc_extent(
            reference["array"],
            source["height"],
            source["width"],
            reference["height"],
            reference["width"],
        )
        # Update reference dict with cropped dimensions
        reference_cropped = {
            "array": ref_cropped,
            "width": reference["width"],
            "height": ref_cropped.shape[0],
            "channels": 1,
            "dtype": reference["dtype"],
            "metadata": reference["metadata"],
        }
        print(f"  TMC-2 cropped: {reference_cropped['width']}x{reference_cropped['height']}")

        # Step 4: Preprocess
        print("\n[4/4] Preprocessing...")
        src_scale = working_scale or analysis["source_working_scale"]
        ref_scale = analysis["reference_working_scale"]
        clahe = apply_clahe if apply_clahe is not None else analysis["recommend_clahe"]

        print(f"  Source working_scale: {src_scale}")
        print(f"  Reference working_scale: {ref_scale}")
        print(f"  CLAHE: {clahe} (clip={clahe_clip})")

        source_preprocessed = preprocess_image(
            source,
            working_scale=src_scale,
            clahe_clip=clahe_clip,
            apply_clahe=clahe,
        )
        reference_preprocessed = preprocess_image(
            reference_cropped,
            working_scale=ref_scale,
            clahe_clip=clahe_clip,
            apply_clahe=False,
        )

        print(f"\n  Source preprocessed: {source_preprocessed['working_width']}x{source_preprocessed['working_height']}")
        print(f"  Reference preprocessed: {reference_preprocessed['working_width']}x{reference_preprocessed['working_height']}")
        print(f"  Source operations: {source_preprocessed['operations']}")
        print(f"  Reference operations: {reference_preprocessed['operations']}")

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runner.py <pair_id>")
        print("Example: python runner.py pair_001")
        sys.exit(1)
    pair_id = sys.argv[1]
    result = run_single(pair_id)
    print("\nDone.")
