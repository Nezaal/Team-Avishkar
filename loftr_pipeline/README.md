# LoFTR OHRC → TMC-2 baseline

This is a **pretrained LoFTR outdoor** baseline for registering one local OHRC region to its TMC-2 reference. It loads only required NPZ tiles from `akshitjn/my-large-dataset`, assembles raw regions, uses the supplied source geometry grids for a coarse initialization, runs LoFTR, estimates a robust affine or homography, and writes visual and machine-readable evidence.

It does not fine-tune or claim independently verified sub-pixel accuracy. `inlier_rmse_tmc2_px` is the inlier fitting residual in native TMC-2 pixels. Independent checkpoints are required before setting `subpixel_accuracy_verified` to true.

## Install on an RTX 3050 6 GB laptop GPU

This repository is tuned for inference on an RTX 3050 with 6 GB VRAM: it uses a 512-pixel LoFTR working image by default and one GPU inference at a time. It is not a fine-tuning configuration.

Your NVIDIA driver must be visible to `nvidia-smi`. Install the CUDA-enabled PyTorch wheel, then install project dependencies. The published CUDA 12.8 index includes a Windows/Python 3.13 wheel; the same index has Python 3.10–3.12 wheels. [PyTorch installation guidance](https://pytorch.org/get-started/locally/)

```bash
git clone <your-repository-url> Team-Avishkar
cd Team-Avishkar
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# Install CUDA-enabled torch for your driver/CUDA version. Do not use a CPU-only wheel.
pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 1024**2, 'MiB')"
```

The model checkpoint downloads automatically on its first use. Keep the Hugging Face cache on persistent storage if the host is ephemeral:

```bash
export HF_HOME=/mnt/persistent/hf-cache
```

## First real run

The currently published HF manifest contains tiles for `pair_001`; choose it for the first run. A run downloads only the tile files intersecting its source and reference regions, then caches them.

```bash
python -m loftr_pipeline.run --pair-id pair_001 --device cuda --source-side 4096 --max-size 512 --model affine --verbose
```

The command prints a run ID. Review `dataset/loftr_runs/<run-id>/report.html`, `result.json`, `correspondences.csv`, and the PNG artifacts. `REGISTERED_UNVERIFIED` means the candidate passed count, coverage, overlap, and geometry gates. It does not mean its physical accuracy was independently validated. `LOW_CONFIDENCE` and `FAILED` still create diagnostic JSON; a failed run may have fewer visual artifacts.

If you see `CUDA out of memory`, retry at `--max-size 384`. Do not run two registration commands at once. Close browsers, games, and other GPU applications before the first run.

For a smaller or manually selected region:

```bash
python -m loftr_pipeline.run --pair-id pair_001 --source-roi 2000,30000,8192,8192 --reference-roi 1000,130000,700,700 --device cuda
```

Manual reference ROIs should be used only after checking the source geometry; an arbitrary same-index tile is not a valid pair.

## API

```bash
uvicorn backend.loftr_api:app --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/pairs
curl -X POST http://127.0.0.1:8000/register -H 'Content-Type: application/json' -d '{"pair_id":"pair_001","device":"cuda"}'
```

`POST /register` returns the result JSON. Artifact endpoints use the returned `run_id`, for example `/runs/<run-id>/artifacts/overlay.png`. The API intentionally serializes inferences: one application worker should own one GPU.

## Outputs

`result.json` contains the result state, exact source and reference ROIs, transform direction, candidate confidence basis, and metrics. The full-native transform maps original OHRC coordinates to original TMC-2 coordinates. `correspondences.csv` has all filtered LoFTR matches, including rejected matches, their LoFTR score, RANSAC inlier flag, and residual when a transformation was estimated.

The pipeline produces `source.png`, `reference.png`, `matches.png`, `registered.png`, `overlay.png`, `checkerboard.png`, `transform.json`, `report.html`, plus native-TMC-2-ROI registered outputs when registration succeeds.

## Preparing the complete dataset

The baseline reads a standard `streaming_dataset/dataset_manifest.json` from the configured HF dataset. Every pair product needs complete tile records and every record must include `product_id`, `rel_filepath`, native row/column bounds, and a NPZ containing `raw` and `mask` arrays. Pairs without both products are listed by `/pairs` but marked `tiles_available: false`.
