"""
ChandraMatch Tile Pair Selector (Module B3 Alias)

Alias module exposing TilePairSelector from backend.pipeline.pair_selector
to ensure full backward compatibility.
"""
from backend.pipeline.pair_selector import TilePairSelector, DEFAULT_MANIFEST

__all__ = ["TilePairSelector", "DEFAULT_MANIFEST"]
