"""
Functional Life Factor (FLF) calculation module.

FLF measures what percentage of an asset's useful life has been consumed,
based on deterioration models specific to each asset type.

Excel formula (clamped):
=IF(ACI=0, 100, IF(ACI>=80, 0, MAX(0, MIN(100, (ConsumedLife/TotalLife)*100))))

Where ConsumedLife = (ACI - intercept) / slope
"""

from typing import Optional
from domain.models import DeteriorationCurve
from domain.lookups.loader import load_flf_equations, get_flf_curve


def calculate_flf(asset_type: str, aci: float) -> float:
    """
    Calculate Functional Life Factor for an asset.
    
    FLF represents the percentage of useful life consumed:
    - ACI = 0 (failed): FLF = 100 (100% life consumed)
    - ACI >= 80 (GOOD): FLF = 0 (minimal life consumed)
    - Otherwise: Based on deterioration curve
    
    The calculation uses asset-specific deterioration equations:
    1. ConsumedLife = (ACI - intercept) / slope
    2. FLF = (ConsumedLife / TotalLife) * 100
    3. Clamp result to 0-100
    
    Args:
        asset_type: Asset type key (e.g., "MANHOLE", "GANTRY_FOUNDATION")
        aci: Asset Condition Index (0-100)
        
    Returns:
        Functional Life Factor (0-100)
        
    Examples:
        >>> calculate_flf("MANHOLE", 100)  # Perfect condition
        0.0
        >>> calculate_flf("MANHOLE", 80)   # Good threshold
        0.0
        >>> calculate_flf("MANHOLE", 0)    # Failed
        100.0
    """
    if aci == 0:
        return 100.0
    if aci >= 80:
        return 0.0
    
    curve = get_flf_curve(asset_type)
    if curve is None:
        return 0.0
    
    flf = curve.calculate_flf(aci)
    return round(flf, 4)


def calculate_flf_with_curve(
    aci: float,
    intercept: float,
    slope: float,
    total_life: float
) -> float:
    """
    Calculate FLF with explicit curve parameters.
    
    Useful when you have the deterioration coefficients directly
    without needing to look up by asset type.
    
    Args:
        aci: Asset Condition Index (0-100)
        intercept: Deterioration equation intercept
        slope: Deterioration equation slope (negative for decay)
        total_life: Total expected life in years
        
    Returns:
        Functional Life Factor (0-100)
    """
    if aci == 0:
        return 100.0
    if aci >= 80:
        return 0.0
    
    consumed_life = (aci - intercept) / slope
    flf = (consumed_life / total_life) * 100
    return max(0.0, min(100.0, round(flf, 4)))


def get_consumed_life(asset_type: str, aci: float) -> Optional[float]:
    """
    Calculate consumed life in years for an asset.
    
    Args:
        asset_type: Asset type key
        aci: Asset Condition Index
        
    Returns:
        Consumed life in years, or None if no curve found
    """
    curve = get_flf_curve(asset_type)
    if curve is None:
        return None
    
    return curve.calculate_consumed_life(aci)


def get_remaining_life(asset_type: str, aci: float) -> Optional[float]:
    """
    Calculate remaining useful life in years for an asset.
    
    Args:
        asset_type: Asset type key
        aci: Asset Condition Index
        
    Returns:
        Remaining life in years, or None if no curve found
    """
    curve = get_flf_curve(asset_type)
    if curve is None:
        return None
    
    consumed = curve.calculate_consumed_life(aci)
    remaining = curve.total_life - consumed
    return max(0.0, remaining)


def get_deterioration_curve(asset_type: str) -> Optional[DeteriorationCurve]:
    """
    Get the deterioration curve for an asset type.
    
    Args:
        asset_type: Asset type key
        
    Returns:
        DeteriorationCurve or None if not found
    """
    return get_flf_curve(asset_type)


def list_asset_types_with_flf() -> list[str]:
    """
    List all asset types that have FLF deterioration curves.
    
    Returns:
        List of asset type keys
    """
    equations = load_flf_equations()
    return list(equations.keys())


ASSETS_WITHOUT_FLF = [
    "LANDSCAPE",
    "DECORATIVE_FURNITURE",
]

FLF_MIN = 0.0
FLF_MAX = 100.0
