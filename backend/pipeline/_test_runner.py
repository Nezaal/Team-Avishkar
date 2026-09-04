import sys
sys.path.insert(0, "backend")
from pipeline.runner import PipelineRunner

runner = PipelineRunner()
result = runner.run_preprocessing("pair_001")

src = result["source_preprocessed"]
ref = result["reference_preprocessed"]

src_img = src["image"]
ref_img = ref["image"]

print("\nVerification:")
print(f"Source (OHRC): {src_img.shape} {src_img.dtype} range=[{src_img.min()},{src_img.max()}]")
print(f"Reference (TMC-2): {ref_img.shape} {ref_img.dtype} range=[{ref_img.min()},{ref_img.max()}]")
print(f"Source working: {src['working_width']}x{src['working_height']}")
print(f"Ref working: {ref['working_width']}x{ref['working_height']}")
print("OK - pipeline works end-to-end")
