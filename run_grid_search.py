import logging
from loftr_pipeline.pipeline import RunConfig, run
from loftr_pipeline.data import TileStore, centered_roi

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def run_grid_search():
    store = TileStore(local_root=".")
    
    pair = store.pair("pair_001")
    source_product = store.products[pair["ohrc_product_id"]]
    source_roi = centered_roi(source_product["width"], source_product["height"], 8192)
    
    # We already know the GPS-predicted base ROI from the previous log
    base_x, base_y, base_w, base_h = 1416, 220871, 744, 714
    
    # Shift by 200 TMC-2 pixels (approx 900 meters) in a grid
    offsets = [-200, 0, 200]
    
    for dy in offsets:
        for dx in offsets:
            x = max(0, base_x + dx)
            y = max(0, base_y + dy)
            
            # Pad the crop for the neural network
            tight_roi = [x - 64, y - 64, base_w + 128, base_h + 128]
            tight_roi[0] = max(0, tight_roi[0])
            tight_roi[1] = max(0, tight_roi[1])
            
            print(f"\n--- Testing Offset: X={dx}, Y={dy} ---")
            
            test_config = RunConfig(
                pair_id="pair_001",
                device="cuda",
                max_size=512,
                local_root=".",
                source_roi=source_roi,
                reference_roi=tight_roi,
                ransac_threshold=5.0
            )
            
            try:
                result = run(test_config, store=store)
                inliers = result.get("metrics", {}).get("inliers", 0)
                
                print(f"Result for offset ({dx}, {dy}): {inliers} inliers")
                
                if result["status"] == "REGISTERED_UNVERIFIED":
                    print(f"\n!!! MATCH FOUND !!! at Offset X={dx}, Y={dy} with {inliers} inliers.")
                    print(f"Run Artifacts saved to: {result['run_id']}")
                    return
            except Exception as e:
                print(f"Failed at ({dx}, {dy}): {e}")

if __name__ == '__main__':
    run_grid_search()
