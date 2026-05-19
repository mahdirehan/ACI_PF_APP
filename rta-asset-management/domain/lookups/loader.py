"""
JSON lookup table loader for RTA calculation engine.

Loads lookup tables from JSON files with caching for performance.
"""

import json
from pathlib import Path
from typing import Optional
from functools import lru_cache

from domain.models import DeteriorationCurve


LOOKUPS_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_rf_scores() -> dict[str, dict]:
    """
    Load Risk Factor scores from rf_scores.json.
    
    Returns:
        Dict mapping asset type key to {name, priority_level, risk_score}
    """
    path = LOOKUPS_DIR / "rf_scores.json"
    with open(path, "r") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_flf_equations() -> dict[str, DeteriorationCurve]:
    """
    Load FLF deterioration equations from flf_equations.json.
    
    Returns:
        Dict mapping asset type key to DeteriorationCurve dataclass
    """
    path = LOOKUPS_DIR / "flf_equations.json"
    with open(path, "r") as f:
        data = json.load(f)
    
    curves = {}
    for key, values in data.items():
        curves[key] = DeteriorationCurve(
            intercept=values["intercept"],
            slope=values["slope"],
            total_life=values["total_life"],
            name=values.get("name", key)
        )
    return curves


@lru_cache(maxsize=1)
def load_asset_types() -> dict[str, list[str]]:
    """
    Load asset type categorization from asset_types.json.
    
    Returns:
        Dict mapping category to list of asset type keys
    """
    path = LOOKUPS_DIR / "asset_types.json"
    with open(path, "r") as f:
        return json.load(f)


@lru_cache(maxsize=50)
def load_defect_mapping(asset_type: str) -> Optional[dict]:
    """
    Load defect-to-score mapping for a specific asset type.
    
    Args:
        asset_type: Asset type key (e.g., "MANHOLE", "GANTRY")
        
    Returns:
        Dict with defect_categories, aci_formula, weights; or None if not found
    """
    normalized = asset_type.upper().replace(" ", "_")
    path = LOOKUPS_DIR / "defects" / f"{normalized.lower()}.json"
    
    if not path.exists():
        return None
    
    with open(path, "r") as f:
        return json.load(f)


def get_defect_score(
    asset_type: str,
    category: str,
    defect_text: str,
    default_score: Optional[float] = None
) -> Optional[float]:
    """
    Look up the score for a defect description.
    
    Implements VLOOKUP-like behavior from Excel sheets.
    
    Args:
        asset_type: Asset type key
        category: Defect category (e.g., "functional", "appearance")
        defect_text: Defect description text to look up
        default_score: Score to return if no match found
        
    Returns:
        Numeric score for the defect, or default_score if not found
    """
    mapping = load_defect_mapping(asset_type)
    if not mapping:
        return default_score
    
    categories = mapping.get("defect_categories", [])
    
    for cat in categories:
        if cat.get("name", "").lower() == category.lower():
            defects = cat.get("defects", [])
            for defect in defects:
                if defect.get("text", "").strip().lower() == defect_text.strip().lower():
                    score = defect.get("score")
                    if score is not None:
                        return float(score)
            
            if "No Defect Found" in defect_text or defect_text.strip() == "":
                max_score = cat.get("max_score")
                if max_score is not None:
                    return float(max_score)
    
    return default_score


def get_rf_score_value(asset_type: str) -> Optional[int]:
    """
    Get raw risk score for an asset type.
    
    Args:
        asset_type: Asset type key
        
    Returns:
        Risk score (60-117 range) or None if not found
    """
    scores = load_rf_scores()
    
    normalized = asset_type.upper().replace(" ", "_")
    
    if normalized in scores:
        return scores[normalized]["risk_score"]
    
    for key, value in scores.items():
        if key.replace("_", "") == normalized.replace("_", ""):
            return value["risk_score"]
        if value.get("name", "").upper().replace(" ", "_") == normalized:
            return value["risk_score"]
    
    return None


def get_flf_curve(asset_type: str) -> Optional[DeteriorationCurve]:
    """
    Get deterioration curve for an asset type.
    
    Args:
        asset_type: Asset type key
        
    Returns:
        DeteriorationCurve or None if not found
    """
    curves = load_flf_equations()
    
    normalized = asset_type.upper().replace(" ", "_")
    
    if normalized in curves:
        return curves[normalized]
    
    for key in curves:
        if key.replace("_", "") == normalized.replace("_", ""):
            return curves[key]
    
    return None


def clear_caches():
    """Clear all cached lookup data. Useful for testing or reloading."""
    load_rf_scores.cache_clear()
    load_flf_equations.cache_clear()
    load_asset_types.cache_clear()
    load_defect_mapping.cache_clear()
