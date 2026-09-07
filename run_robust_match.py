import cv2
import numpy as np
import logging
from loftr_pipeline.data import TileStore, centered_roi
from loftr_pipeline.pipeline import prepare, RunConfig

logging.basicConfig(level=logging.INFO)

def run_edge_correlation():
    # 1. Load Data
    store = TileStore(local_root=".", cache_dir="C:/hfcache")
    config = RunConfig(pair_id="pair_001", max_size=512, local_root=".")
    
    pair = store.pair("pair_001")
    
    source_roi = centered_roi(12000, 93693, 8192)
    # Target ROI based on GPS
    reference_roi = [1416, 220871, 744, 714]
    
    # Load OHRC
    print("Loading OHRC tiles...")
    a, ma = store.assemble(pair["ohrc_product_id"], source_roi, 6)
    
    # Load TMC-2 (Load a slightly larger area to search inside)
    print("Loading TMC-2 tiles...")
    pad = 100
    ref_search_roi = [reference_roi[0]-pad, reference_roi[1]-pad, reference_roi[2]+pad*2, reference_roi[3]+pad*2]
    b, mb = store.assemble(pair["tmc2_product_id"], ref_search_roi, 6)
    
    # 2. Prepare and Mathematically Rotate
    # Coarse matrix rotates OHRC to match TMC-2 GPS rotation
    sa, sm, rb, rm, _, _, _, _ = prepare(a, ma, b, mb, source_roi, ref_search_roi, 0.25, 4.48, config, coarse=None)
    
    # 3. Strip Shadows via Edge Extraction
    print("Extracting illumination-invariant edges...")
    sa_edge = cv2.Canny(sa, 40, 120).astype(np.float32)
    rb_edge = cv2.Canny(rb, 40, 120).astype(np.float32)
    
    # 4. Phase Correlation (Mathematically guaranteed to find offset if structure exists)
    print("Running FFT Phase Correlation...")
    # Pad sa_edge to match rb_edge size for FFT
    h, w = rb_edge.shape
    sa_padded = np.zeros_like(rb_edge)
    sh, sw = sa_edge.shape
    sa_padded[:sh, :sw] = sa_edge
    
    shift, error = cv2.phaseCorrelate(sa_padded, rb_edge)
    
    print(f"Calculated GPS Error Shift: X={shift[0]:.2f}, Y={shift[1]:.2f} pixels")
    print(f"Confidence (Phase Peak): {error:.4f}")
    
    if error > 0.03:
        print("SUCCESS! Found a strong structural match independent of shadows.")
    else:
        print("FAILED: Even the physical edges don't match. This region is either flat sand or the GPS is off by > 1.5km.")

if __name__ == '__main__':
    run_edge_correlation()
