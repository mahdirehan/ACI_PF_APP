"""
Risk Factor (RF) calculation module.

RF measures the inherent risk/importance of an asset type.
It's based on predefined risk scores normalized to a 10-100 scale.

Excel formula: =10+((Score-MIN(All_Scores))/(MAX(All_Scores)-MIN(All_Scores)))*(100-10)
"""

from typing import Optional
from domain.lookups.loader import load_rf_scores, get_rf_score_value


_RF_CACHE: dict[str, float] = {}


def calculate_rf(asset_type: str) -> float:
    """
    Calculate Risk Factor for an asset type.
    
    RF is determined by the asset type's inherent risk score, which is
    then min-max normalized to a 10-100 scale across all asset types.
    
    Excel formula: =10+((Score-MIN)/(MAX-MIN))*(100-10)
    
    This ensures:
    - Minimum RF = 10 (for lowest-risk assets like Benches)
    - Maximum RF = 100 (for highest-risk assets like Traffic Signals)
    
    Args:
        asset_type: Asset type key (e.g., "TRAFFIC_SIGNAL", "MANHOLE")
        
    Returns:
        Risk Factor (10-100)
        
    Raises:
        ValueError: If asset type not found in RF scores
        
    Examples:
        >>> calculate_rf("TRAFFIC_SIGNAL")  # Highest risk (117)
        100.0
        >>> calculate_rf("BENCHES")  # Lowest risk (60)
        10.0
    """
    if asset_type in _RF_CACHE:
        return _RF_CACHE[asset_type]
    
    rf_scores = load_rf_scores()
    
    score = get_rf_score_value(asset_type)
    if score is None:
        raise ValueError(f"No RF score found for asset type: {asset_type}")
    
    all_scores = [v["risk_score"] for v in rf_scores.values()]
    min_score = min(all_scores)
    max_score = max(all_scores)
    
    if max_score == min_score:
        rf = 50.0
    else:
        rf = 10 + ((score - min_score) / (max_score - min_score)) * 90
    
    rf = round(rf, 4)
    _RF_CACHE[asset_type] = rf
    return rf


def get_rf_for_asset(asset_type: str, default: Optional[float] = None) -> Optional[float]:
    """
    Get RF for an asset type, returning default if not found.
    
    Args:
        asset_type: Asset type key
        default: Value to return if asset not found
        
    Returns:
        Risk Factor or default value
    """
    try:
        return calculate_rf(asset_type)
    except ValueError:
        return default


def get_all_rf_values() -> dict[str, float]:
    """
    Calculate RF values for all known asset types.
    
    Returns:
        Dict mapping asset type to RF value
    """
    rf_scores = load_rf_scores()
    return {asset_type: calculate_rf(asset_type) for asset_type in rf_scores}


def get_priority_level(asset_type: str) -> str:
    """
    Get the priority level (H/M/L) for an asset type.
    
    Args:
        asset_type: Asset type key
        
    Returns:
        Priority level string ("H", "M", or "L")
    """
    rf_scores = load_rf_scores()
    normalized = asset_type.upper().replace(" ", "_")
    
    if normalized in rf_scores:
        return rf_scores[normalized].get("priority_level", "M")
    
    for key, value in rf_scores.items():
        if key.replace("_", "") == normalized.replace("_", ""):
            return value.get("priority_level", "M")
    
    return "M"


RF_MIN = 10.0
RF_MAX = 100.0
