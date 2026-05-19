"""
Weighted ACI calculator for assets with non-standard component splits.

Handles two patterns:
1. 70/30 weighted: ACI = F*0.7 + A*0.3 (Bollards, Road Marking)
2. 80/20 weighted: ACI = F*0.8 + A*0.2 (Barrier)

Excel formula examples:
- Bollards: =K3*0.7 + K3*0.3 (where K3 is base score)
- Road Marking: =M3*0.7 + M3*0.3
- Barrier: =K3*0.8 + K3*0.2
"""

from typing import Optional
from domain.models import DefectInput, ACIResult, get_aci_rating
from domain.aci.defect_mapper import DefectMapper


WEIGHTED_70_30_ASSETS = ["BOLLARDS", "ROAD_MARKING", "ROAD_MARKING_SYMBOL"]
WEIGHTED_80_20_ASSETS = ["BARRIER"]


def calculate_weighted_70_30(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI with 70/30 weighting.
    
    Formula: ACI = Functional*0.7 + Appearance*0.3
    Or for road marking: ACI = Visibility*0.7 + Presence*0.3
    
    Args:
        asset_type: Asset type key (BOLLARDS, ROAD_MARKING, ROAD_MARKING_SYMBOL)
        defects: DefectInput with appropriate defect fields
        
    Returns:
        ACIResult with weighted scores
    """
    asset_upper = asset_type.upper().replace(" ", "_")
    mapper = DefectMapper(asset_upper)
    
    if asset_upper in ["ROAD_MARKING", "ROAD_MARKING_SYMBOL"]:
        return _calculate_road_marking(asset_upper, defects, mapper)
    else:
        return _calculate_bollards(defects, mapper)


def _calculate_bollards(defects: DefectInput, mapper: DefectMapper) -> ACIResult:
    """Calculate ACI for Bollards with 70/30 F/A weighting."""
    functional_defect = defects.functional_defect or "No Defect Found"
    appearance_defect = defects.appearance_defect or "No Defect Found"
    
    base_score = _get_base_score_from_defects(mapper, functional_defect, appearance_defect)
    
    f_score = base_score * 0.7
    a_score = base_score * 0.3
    
    aci = f_score + a_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "functional": round(f_score, 2),
            "appearance": round(a_score, 2),
            "base_score": base_score
        },
        formula="F*0.7 + A*0.3"
    )


def _calculate_road_marking(
    asset_type: str,
    defects: DefectInput,
    mapper: DefectMapper
) -> ACIResult:
    """
    Calculate ACI for Road Marking with visibility/presence weighting.
    
    Can use retroreflectivity measurement or defect dropdowns.
    """
    visibility_defect = defects.visibility_defect or defects.functional_defect or "No Defect Found"
    presence_defect = defects.presence_defect or defects.appearance_defect or "No Defect Found"
    
    if defects.retroreflectivity_value is not None:
        v_score = _calculate_visibility_from_retroreflectivity(
            defects.retroreflectivity_value,
            defects.observation_angle,
            defects.entrance_angle,
            defects.color
        )
    else:
        base_score = _get_base_score_from_defects(mapper, visibility_defect, presence_defect)
        v_score = base_score * 0.7
    
    p_score = mapper.get_score("presence", presence_defect)
    if p_score is None:
        p_score = mapper.get_score("appearance", presence_defect)
    if p_score is None:
        base_score = _get_base_score_from_defects(mapper, visibility_defect, presence_defect)
        p_score = base_score * 0.3
    
    aci = v_score + p_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "visibility": round(v_score, 2),
            "presence": round(p_score, 2)
        },
        formula="V*0.7 + P*0.3"
    )


def _calculate_visibility_from_retroreflectivity(
    rl_value: float,
    observation_angle: Optional[str] = None,
    entrance_angle: Optional[str] = None,
    color: Optional[str] = None
) -> float:
    """
    Calculate visibility score from retroreflectivity measurement.
    
    Excel formula: =ROUND(70*(RL_Value/Threshold), 0)
    Where threshold depends on road type and marking color.
    """
    threshold = 100.0
    
    if color:
        color_lower = color.lower()
        if "white" in color_lower:
            threshold = 100.0
        elif "yellow" in color_lower:
            threshold = 80.0
    
    visibility = min(70, round(70 * (rl_value / threshold), 0))
    return max(0, visibility)


def _get_base_score_from_defects(
    mapper: DefectMapper,
    functional_defect: str,
    appearance_defect: str
) -> float:
    """
    Get base score (100 for no defect, lower for defects).
    
    Used when the Excel sheet uses a single base score multiplied by weights.
    """
    f_defect_lower = functional_defect.lower()
    a_defect_lower = appearance_defect.lower()
    
    if "no defect" in f_defect_lower and "no defect" in a_defect_lower:
        return 100.0
    
    f_score = mapper.get_score("functional", functional_defect)
    if f_score is not None:
        return f_score / 0.7 if f_score <= 70 else f_score
    
    if "minor" in f_defect_lower or "minor" in a_defect_lower:
        return 90.0
    elif "damage" in f_defect_lower or "faded" in a_defect_lower:
        return 70.0
    elif "major" in f_defect_lower or "severe" in a_defect_lower:
        return 40.0
    
    return 100.0


def calculate_weighted_80_20(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI with 80/20 weighting.
    
    Formula: ACI = Functional*0.8 + Appearance*0.2
    Used for Barrier asset type.
    
    Args:
        asset_type: Asset type key (BARRIER)
        defects: DefectInput with functional_defect and appearance_defect
        
    Returns:
        ACIResult with weighted scores
    """
    mapper = DefectMapper("BARRIER")
    
    functional_defect = defects.functional_defect or "No Defect Found"
    appearance_defect = defects.appearance_defect or "No Defect Found"
    
    base_score = _get_base_score_from_defects(mapper, functional_defect, appearance_defect)
    
    f_score = base_score * 0.8
    a_score = base_score * 0.2
    
    aci = f_score + a_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "functional": round(f_score, 2),
            "appearance": round(a_score, 2),
            "base_score": base_score
        },
        formula="F*0.8 + A*0.2"
    )


def calculate(asset_type: str, defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for any weighted asset type.
    
    Dispatches to 70/30 or 80/20 calculation based on asset type.
    
    Args:
        asset_type: Asset type key
        defects: DefectInput
        
    Returns:
        ACIResult
    """
    asset_upper = asset_type.upper().replace(" ", "_")
    
    if asset_upper in WEIGHTED_80_20_ASSETS:
        return calculate_weighted_80_20(asset_upper, defects)
    else:
        return calculate_weighted_70_30(asset_upper, defects)
