"""
Lookup table loaders for RTA calculation engine.

Provides functions to load JSON lookup tables for:
- RF (Risk Factor) scores
- FLF (Functional Life Factor) deterioration equations  
- Defect-to-score mappings per asset type
"""

from domain.lookups.loader import (
    load_rf_scores,
    load_flf_equations,
    load_defect_mapping,
    load_asset_types,
    get_defect_score,
)

__all__ = [
    "load_rf_scores",
    "load_flf_equations", 
    "load_defect_mapping",
    "load_asset_types",
    "get_defect_score",
]
