"""
Priority Factor aggregator module.

Combines Condition Factor (CF), Risk Factor (RF), and Functional Life Factor (FLF)
into a single Priority Factor score using configurable weights.

PF = CF_weight * CF + RF_weight * RF + FLF_weight * FLF
"""

from typing import Optional
from domain.models import PFResult
from domain.pf.cf import calculate_cf
from domain.pf.rf import calculate_rf
from domain.pf.flf import calculate_flf


DEFAULT_WEIGHTS = {
    "cf": 0.60,
    "rf": 0.20,
    "flf": 0.20,
}


def calculate_pf(
    asset_type: str,
    aci: float,
    weights: Optional[dict[str, float]] = None,
    risk_score_override: Optional[int] = None,
) -> PFResult:
    """
    Calculate Priority Factor for an asset.
    
    PF aggregates three factors with configurable weights:
    - CF (Condition Factor): How deteriorated the asset is
    - RF (Risk Factor): Inherent risk/importance of asset type
    - FLF (Functional Life Factor): Percentage of useful life consumed
    
    Default weights: CF=60%, RF=20%, FLF=20%
    
    Args:
        asset_type: Asset type key (e.g., "MANHOLE", "GANTRY")
        aci: Asset Condition Index (0-100)
        weights: Optional custom weights dict with keys "cf", "rf", "flf"
        risk_score_override: Optional aggregated total from a per-asset
            :class:`domain.risk.RiskAssessment`. When supplied, RF is derived
            by direct clamping into [10, 100] instead of the legacy
            per-asset-type lookup.
        
    Returns:
        PFResult with pf, cf, rf, flf values and weights used
        
    Examples:
        >>> result = calculate_pf("MANHOLE", 60)
        >>> result.pf  # PF score from legacy RF lookup
        >>> result = calculate_pf("MANHOLE", 60, risk_score_override=87)
        >>> result.rf  # 87.0 (user-driven, clamped)
    """
    cf_value = calculate_cf(aci)
    rf_value = calculate_rf(asset_type, override_score=risk_score_override)
    flf_value = calculate_flf(asset_type, aci)
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    w_cf = weights.get("cf", DEFAULT_WEIGHTS["cf"])
    w_rf = weights.get("rf", DEFAULT_WEIGHTS["rf"])
    w_flf = weights.get("flf", DEFAULT_WEIGHTS["flf"])
    
    pf_value = (
        w_cf * cf_value +
        w_rf * rf_value +
        w_flf * flf_value
    )
    
    return PFResult(
        pf=round(pf_value, 2),
        cf=round(cf_value, 2),
        rf=round(rf_value, 2),
        flf=round(flf_value, 2),
        aci=aci,
        weights={"cf": w_cf, "rf": w_rf, "flf": w_flf}
    )


def calculate_pf_batch(
    assets: list[tuple[str, float]],
    weights: Optional[dict[str, float]] = None
) -> list[PFResult]:
    """
    Calculate PF for multiple assets efficiently.
    
    Args:
        assets: List of (asset_type, aci) tuples
        weights: Optional weights to use for all assets
        
    Returns:
        List of PFResult objects in same order as input
    """
    return [calculate_pf(asset_type, aci, weights) for asset_type, aci in assets]


def recalculate_pf_with_weights(
    cf: float,
    rf: float,
    flf: float,
    weights: dict[str, float]
) -> float:
    """
    Recalculate PF from component values with new weights.
    
    Useful for "what-if" analysis when changing weight configuration.
    
    Args:
        cf: Condition Factor value
        rf: Risk Factor value
        flf: Functional Life Factor value
        weights: Weight dict with "cf", "rf", "flf" keys
        
    Returns:
        New PF value
    """
    return (
        weights.get("cf", 0.6) * cf +
        weights.get("rf", 0.2) * rf +
        weights.get("flf", 0.2) * flf
    )


def get_pf_rank_order(
    pf_results: list[PFResult],
    descending: bool = True
) -> list[tuple[int, PFResult]]:
    """
    Rank assets by Priority Factor.
    
    Args:
        pf_results: List of PFResult objects
        descending: If True, highest PF first (default for maintenance priority)
        
    Returns:
        List of (rank, PFResult) tuples sorted by PF
    """
    sorted_results = sorted(
        enumerate(pf_results),
        key=lambda x: x[1].pf,
        reverse=descending
    )
    return [(rank + 1, result) for rank, (_, result) in enumerate(sorted_results)]


def validate_weights(weights: dict[str, float]) -> bool:
    """
    Validate that PF weights sum to 1.0 (within tolerance).
    
    Args:
        weights: Weight dict with "cf", "rf", "flf" keys
        
    Returns:
        True if weights are valid
    """
    total = sum(weights.values())
    return abs(total - 1.0) < 0.001
