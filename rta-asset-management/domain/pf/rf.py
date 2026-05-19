"""
Risk Factor (RF) calculation module.

RF measures the inherent risk/importance of an asset type.

Two paths are supported:

1. Legacy lookup: a predefined per-asset-type risk score (from
   ``rf_scores.json``) is min-max normalized to a 10-100 scale across all
   asset types. Excel formula:
   ``=10+((Score-MIN(All_Scores))/(MAX(All_Scores)-MIN(All_Scores)))*(100-10)``

2. Per-asset override: a user-entered total from a :class:`RiskAssessment`
   (sum of 4 OAMP categories, each Probability x Impact) is mapped to RF by
   direct clamping into [10, 100] via :func:`domain.risk.total_to_rf`. The
   total naturally falls in [4, 100], so the clamp only floors very-low-risk
   assets at RF=10.
"""

from typing import Optional, Tuple
from domain.lookups.loader import load_rf_scores, get_rf_score_value
from domain.risk.aggregator import total_to_rf
from domain.risk.models import RiskAssessment


_RF_CACHE: dict[Tuple[str, Optional[int]], float] = {}


def calculate_rf(
    asset_type: str,
    override_score: Optional[int] = None,
) -> float:
    """
    Calculate Risk Factor for an asset.
    
    When ``override_score`` is provided (typically the aggregated total from a
    per-asset :class:`RiskAssessment`), RF is the direct-clamp mapping
    ``max(10, min(100, override_score))``. The legacy min-max pool is skipped
    so the user's input fully drives the result.
    
    When ``override_score`` is ``None``, the legacy per-asset-type lookup
    runs and produces the historical behavior:
    - Minimum RF = 10 (for lowest-risk assets like Benches)
    - Maximum RF = 100 (for highest-risk assets like Traffic Signals)
    
    Args:
        asset_type: Asset type key (e.g., "TRAFFIC_SIGNAL", "MANHOLE")
        override_score: Optional per-asset aggregated risk total (4-100)
    
    Returns:
        Risk Factor (10-100)
    
    Raises:
        ValueError: If no override is supplied and the asset type is not
            present in the legacy RF score lookup.
    
    Examples:
        >>> calculate_rf("TRAFFIC_SIGNAL")  # Legacy lookup, highest risk
        100.0
        >>> calculate_rf("BENCHES")  # Legacy lookup, lowest risk
        10.0
        >>> calculate_rf("MANHOLE", override_score=87)  # User-driven
        87.0
    """
    cache_key = (asset_type, override_score)
    if cache_key in _RF_CACHE:
        return _RF_CACHE[cache_key]
    
    if override_score is not None:
        rf = total_to_rf(override_score)
        _RF_CACHE[cache_key] = rf
        return rf
    
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
    _RF_CACHE[cache_key] = rf
    return rf


def calculate_rf_from_assessment(assessment: RiskAssessment) -> float:
    """
    Convenience wrapper: derive RF directly from a :class:`RiskAssessment`.
    
    Equivalent to ``calculate_rf(assessment.asset_type,
    override_score=assessment.total_score)``.
    """
    return calculate_rf(
        assessment.asset_type,
        override_score=assessment.total_score,
    )


def get_rf_for_asset(
    asset_type: str,
    default: Optional[float] = None,
    override_score: Optional[int] = None,
) -> Optional[float]:
    """
    Get RF for an asset, returning ``default`` if no value can be derived.
    
    Args:
        asset_type: Asset type key
        default: Value to return if asset not found (legacy path only)
        override_score: Optional per-asset aggregated risk total. When set,
            the function always returns ``calculate_rf(asset_type,
            override_score=...)`` since that path never raises.
    
    Returns:
        Risk Factor or default value
    """
    try:
        return calculate_rf(asset_type, override_score=override_score)
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
