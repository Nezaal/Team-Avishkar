import os

file_path = 'backend/pipeline/generate_full_dataset.py'
with open(file_path, 'r') as f:
    content = f.read()

# Make sure we don't double-patch
if 'max_workers' in content:
    print("Already patched.")
    exit(0)

# Replace args
content = content.replace(
    'parser.add_argument("--checkpoint-interval"',
    'parser.add_argument("--workers", type=int, default=1, help="Number of concurrent network threads")\n    parser.add_argument("--checkpoint-interval"'
)
content = content.replace(
    'generator.run_full_generation(limit_products=args.limit_products, ohrc_only=args.ohrc_only, tmc2_only=args.tmc2_only)',
    'generator.run_full_generation(limit_products=args.limit_products, ohrc_only=args.ohrc_only, tmc2_only=args.tmc2_only, max_workers=args.workers)'
)
content = content.replace(
    'def run_full_generation(self, limit_products: Optional[int] = None, ohrc_only: bool = False, tmc2_only: bool = False) -> bool:',
    'def run_full_generation(self, limit_products: Optional[int] = None, ohrc_only: bool = False, tmc2_only: bool = False, max_workers: int = 1) -> bool:'
)
content = content.replace(
    'success = self.generate_product(prod_idx, p)',
    'success = self.generate_product(prod_idx, p, max_workers=max_workers)'
)
content = content.replace(
    'def generate_product(self, prod_idx: int, product: Dict[str, Any]) -> bool:',
    'def generate_product(self, prod_idx: int, product: Dict[str, Any], max_workers: int = 1) -> bool:'
)

loop_start = '        # Iterate over row strips (stride = 512)\n        for r_idx in range(n_rows):'
loop_end = '        # Product Completion Validation'
start_idx = content.find(loop_start)
end_idx = content.find(loop_end)

original_loop = content[start_idx:end_idx]

# Replace the loop definition
inner_body = original_loop.replace('        for r_idx in range(n_rows):', '        def _process_row_strip(r_idx):\n            nonlocal prod_bytes_written, prod_network_bytes, prod_http_requests, prod_new_tiles')

# Fix outer loop continue
inner_body = inner_body.replace(
'''            if all(tid in done_tiles for tid in strip_tile_ids):
                continue''', 
'''            if all(tid in done_tiles for tid in strip_tile_ids):
                return True'''
)

# Lock thread-unsafe operations
inner_body = inner_body.replace(
    'self.total_http_requests += 1', 
    'with self.manifest_lock:\n                    self.total_http_requests += 1'
)
inner_body = inner_body.replace(
    'self.total_network_bytes += strip_bytes', 
    'with self.manifest_lock:\n                    self.total_network_bytes += strip_bytes'
)
inner_body = inner_body.replace(
    'self.total_bytes_written += written_size', 
    'with self.manifest_lock:\n                        self.total_bytes_written += written_size'
)
inner_body = inner_body.replace(
    'self.total_tiles_generated += 1', 
    'with self.manifest_lock:\n                        self.total_tiles_generated += 1'
)
inner_body = inner_body.replace(
    'self.manifest["tiles"][tile_id] = tile_record', 
    'with self.manifest_lock:\n                        self.manifest["tiles"][tile_id] = tile_record'
)
inner_body = inner_body.replace(
    'done_tiles[tile_id] = tile_record', 
    'with self.manifest_lock:\n                        done_tiles[tile_id] = tile_record'
)
inner_body = inner_body.replace(
    'self.manifest["total_tiles"] = len(self.manifest["tiles"])', 
    'with self.manifest_lock:\n                    self.manifest["total_tiles"] = len(self.manifest["tiles"])'
)

# Return true at end of function
inner_body = inner_body + '            return True\n'


execution_logic = '''
        # Iterate over row strips
        if max_workers <= 1:
            for r_idx in range(n_rows):
                if _process_row_strip(r_idx) is False:
                    return False
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_process_row_strip, r) for r in range(n_rows)]
                for future in as_completed(futures):
                    if future.result() is False:
                        return False
'''

new_content = content[:start_idx] + inner_body + execution_logic + '\n' + content[end_idx:]

with open(file_path, 'w') as f:
    f.write(new_content)

print("SUCCESS")
