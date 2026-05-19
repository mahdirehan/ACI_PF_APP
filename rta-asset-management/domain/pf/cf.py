"""
Condition Factor (CF) calculation module.

CF measures how far an asset's condition has deteriorated from the "good" threshold.
It's a linear scale that increases as condition worsens.

Excel formula: =IF(ACI>=80, 0, (80-ACI)/80*100)
"""


def calculate_cf(aci: float) -> float:
    """
    Calculate Condition Factor from Asset Condition Index.
    
    CF represents the priority boost due to poor condition:
    - ACI >= 80 (GOOD): CF = 0 (no condition-based priority)
    - ACI = 0 (worst): CF = 100 (maximum priority)
    - Linear interpolation between 0-80
    
    This implements the Excel formula from the Condition Factor sheet:
    =IF(ACI>=80, 0, (80-ACI)/80*100)
    
    Args:
        aci: Asset Condition Index (0-100)
        
    Returns:
        Condition Factor (0-100)
        
    Examples:
        >>> calculate_cf(100)  # Perfect condition
        0.0
        >>> calculate_cf(80)   # Good threshold
        0.0
        >>> calculate_cf(40)   # Fair condition
        50.0
        >>> calculate_cf(0)    # Worst condition
        100.0
    """
    if aci >= 80:
        return 0.0
    
    cf = (80 - aci) / 80 * 100
    return round(cf, 4)


def calculate_cf_from_lookup(aci: int) -> float:
    """
    Calculate CF using the 101-row lookup table approach.
    
    For integer ACI values 0-100, this gives exact Excel parity.
    For non-integer values, use calculate_cf() instead.
    
    Args:
        aci: Integer ACI value (0-100)
        
    Returns:
        Condition Factor value
    """
    aci = max(0, min(100, int(aci)))
    return calculate_cf(float(aci))


CF_THRESHOLD = 80
CF_MAX = 100.0
CF_MIN = 0.0
