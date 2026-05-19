"""
Main ACI calculator dispatcher.

Routes ACI calculations to the appropriate module based on asset type category.
"""

from domain.models import (
    AssetType, 
    AssetCategory, 
    DefectInput, 
    ACIResult,
    ASSET_CATEGORIES,
    get_asset_category
)
from domain.aci import simple, weighted, complex as complex_aci


def calculate_aci(
    asset_type: str | AssetType,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate Asset Condition Index for any asset type.
    
    This is the main entry point for ACI calculation. It dispatches to
    the appropriate calculation module based on the asset type's category.
    
    Args:
        asset_type: Asset type key or AssetType enum
        defects: DefectInput with defect descriptions
        
    Returns:
        ACIResult with aci score, rating, and component scores
        
    Raises:
        ValueError: If asset type is not recognized
        
    Examples:
        >>> defects = DefectInput(functional_defect="No Defect Found", appearance_defect="No Defect Found")
        >>> result = calculate_aci(AssetType.MANHOLE, defects)
        >>> result.aci
        100.0
        >>> result.rating
        <ACIRating.GOOD: 'GOOD'>
    """
    if isinstance(asset_type, AssetType):
        asset_key = asset_type.value
    else:
        asset_key = str(asset_type).upper().replace(" ", "_")
    
    category = _get_category_for_asset(asset_key)
    
    if category == AssetCategory.SIMPLE_F_A:
        return simple.calculate(asset_key, defects)
    elif category == AssetCategory.FUNCTIONAL_ONLY:
        return simple.calculate_functional_only(asset_key, defects)
    elif category == AssetCategory.WEIGHTED_70_30:
        return weighted.calculate_weighted_70_30(asset_key, defects)
    elif category == AssetCategory.WEIGHTED_80_20:
        return weighted.calculate_weighted_80_20(asset_key, defects)
    elif category == AssetCategory.COMPLEX:
        return complex_aci.calculate(asset_key, defects)
    else:
        return simple.calculate(asset_key, defects)


def _get_category_for_asset(asset_key: str) -> AssetCategory:
    """
    Determine the calculation category for an asset type.
    
    First checks the ASSET_CATEGORIES mapping, then falls back to
    checking against known asset lists.
    """
    try:
        asset_type = AssetType(asset_key)
        if asset_type in ASSET_CATEGORIES:
            return ASSET_CATEGORIES[asset_type]
    except ValueError:
        pass
    
    if asset_key in simple.SIMPLE_F_A_ASSETS:
        return AssetCategory.SIMPLE_F_A
    elif asset_key in simple.FUNCTIONAL_ONLY_ASSETS:
        return AssetCategory.FUNCTIONAL_ONLY
    elif asset_key in weighted.WEIGHTED_70_30_ASSETS:
        return AssetCategory.WEIGHTED_70_30
    elif asset_key in weighted.WEIGHTED_80_20_ASSETS:
        return AssetCategory.WEIGHTED_80_20
    elif asset_key in complex_aci.COMPLEX_ASSETS:
        return AssetCategory.COMPLEX
    
    return AssetCategory.SIMPLE_F_A


def calculate_aci_from_scores(
    functional_score: float,
    appearance_score: float = 0.0,
    formula: str = "F + A"
) -> ACIResult:
    """
    Calculate ACI directly from component scores.
    
    Useful when scores are already known (e.g., from database).
    
    Args:
        functional_score: Functional component score
        appearance_score: Appearance component score (default 0)
        formula: Formula description for result
        
    Returns:
        ACIResult
    """
    aci = functional_score + appearance_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "functional": functional_score,
            "appearance": appearance_score
        },
        formula=formula
    )


def calculate_aci_batch(
    items: list[tuple[str, DefectInput]]
) -> list[ACIResult]:
    """
    Calculate ACI for multiple assets.
    
    Args:
        items: List of (asset_type, defects) tuples
        
    Returns:
        List of ACIResult in same order as input
    """
    return [calculate_aci(asset_type, defects) for asset_type, defects in items]


def get_supported_asset_types() -> list[str]:
    """
    Get list of all supported asset types.
    
    Returns:
        List of asset type keys
    """
    return [at.value for at in AssetType]
