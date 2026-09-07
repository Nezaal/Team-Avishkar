"""CLI entry point for the pretrained LoFTR registration baseline."""
import argparse
import json
import logging
import sys

from .pipeline import RunConfig, run


def roi(value):
    try:
        values = [int(x.strip()) for x in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ROI must be x,y,width,height") from exc
    if len(values) != 4:
        raise argparse.ArgumentTypeError("ROI must be x,y,width,height")
    return values


def main():
    parser = argparse.ArgumentParser(description="Register a local OHRC ROI to TMC-2 with pretrained LoFTR")
    parser.add_argument("--pair-id", default="pair_001")
    parser.add_argument("--repo-id", default="akshitjn/my-large-dataset")
    parser.add_argument("--revision", default="main", help="HF revision; resolved to a commit SHA at runtime")
    parser.add_argument("--geometry-repo", default="Nezaal/pradan-dataset")
    parser.add_argument("--local-root", help="Dataset root used before HF cache")
    parser.add_argument("--offline", action="store_true", help="Never make network requests")
    parser.add_argument("--source-roi", type=roi, help="OHRC ROI: x,y,width,height")
    parser.add_argument("--reference-roi", type=roi, help="TMC-2 ROI: x,y,width,height; requires --source-roi")
    parser.add_argument("--source-side", type=int, default=8192)
    parser.add_argument("--max-size", type=int, default=512, help="Maximum LoFTR side length; 512 is safe for 6 GB GPUs")
    parser.add_argument("--model", choices=("affine", "homography"), default="affine")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--min-confidence", type=float, default=.5)
    parser.add_argument("--ransac-threshold", type=float, default=2.)
    parser.add_argument("--clahe", action="store_true")
    parser.add_argument("--output-root", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    values = vars(args).copy()
    values.pop("verbose")
    values["ransac_threshold"] = values.pop("ransac_threshold")
    if values.get("output_root") is None:
        values.pop("output_root")
    result = run(RunConfig(**values))
    print(json.dumps({k: result.get(k) for k in ("run_id", "pair_id", "status", "reason", "metrics", "elapsed_seconds", "artifacts")}, indent=2))
    return 0 if result["status"] in ("REGISTERED_UNVERIFIED", "LOW_CONFIDENCE", "FAILED") else 1


if __name__ == "__main__":
    sys.exit(main())
