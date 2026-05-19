"""
Simple ACI calculator for standard asset types.

Handles two patterns:
1. F + A = 100 (Functional 80 + Appearance 20)
2. F = 100 (Functional only)

Excel formula examples:
- Simple: ACI = F + A
- F-only: ACI = F
"""

from typing import Optional
from domain.models import DefectInput, ACIResult, ACIRating, get_aci_rating
from domain.aci.defect_mapper import DefectMapper


SIMPLE_F_A_ASSETS = [
    "MANHOLE", "GULLY", "CURBSTONE", "GUARDRAIL", "FENCE", "HUMP",
    "BENCH", "CYCLE_RACK", "WOODEN_DECK", "JOGGING_TRACK", "ROAD_SIGN_POLE",
    "DRAINAGE_POINT", "CRASH_CUSHION", "CRASH_CUSHION_END_TERMINAL"
]

FUNCTIONAL_ONLY_ASSETS = [
    "ROAD_STUD", "FOOTPATH", "CAMEL_GRID", "CONTROL_CABINET",
    "ROADSIDE_CAMERA", "DECORATIVE_FURNITURE", "LANDSCAPE",
    "PARKING", "LABAY", "SHOULDER", "ISLAND"
]


def calculate_simple_fa(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI for simple F+A assets.
    
    Formula: ACI = Functional_Score + Appearance_Score
    Where: F max = 80, A max = 20, total max = 100
    
    Args:
        asset_type: Asset type key
        defects: DefectInput with functional_defect and appearance_defect
        
    Returns:
        ACIResult with aci, rating, and component scores
    """
    mapper = DefectMapper(asset_type)
    
    functional_defect = defects.functional_defect or "No Defect Found"
    appearance_defect = defects.appearance_defect or "No Defect Found"
    
    f_score = mapper.get_score("functional", functional_defect)
    if f_score is None:
        if "no defect" in functional_defect.lower():
            f_score = mapper.get_max_score("functional")
        else:
            f_score = 0.0
    
    a_score = mapper.get_score("appearance", appearance_defect)
    if a_score is None:
        if "no defect" in appearance_defect.lower():
            a_score = mapper.get_max_score("appearance")
        else:
            a_score = 0.0
    
    aci = f_score + a_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "functional": f_score,
            "appearance": a_score
        },
        formula="F + A"
    )


def calculate_functional_only(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI for functional-only assets.
    
    Formula: ACI = Functional_Score
    These assets don't have separate appearance ratings.
    
    Args:
        asset_type: Asset type key
        defects: DefectInput with functional_defect
        
    Returns:
        ACIResult with aci, rating, and component scores
    """
    mapper = DefectMapper(asset_type)
    
    functional_defect = defects.functional_defect or "No Defect Found"
    
    f_score = mapper.get_score("functional", functional_defect)
    if f_score is None:
        if "no defect" in functional_defect.lower():
            f_score = 100.0
        else:
            f_score = 0.0
    
    aci = max(0, min(100, f_score))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "functional": f_score
        },
        formula="F"
    )


def calculate_drainage_point(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Drainage Point.
    
    Formula: ACI = Blockage_Score + Concrete_Damage_Score
    Each component max = 50, total = 100
    """
    mapper = DefectMapper("DRAINAGE_POINT")
    
    blockage_defect = defects.blockage_defect or defects.functional_defect or "No Defect Found"
    concrete_defect = defects.concrete_damage_defect or defects.appearance_defect or "No Defect Found"
    
    bl_score = mapper.get_score("blockage", blockage_defect)
    if bl_score is None:
        bl_score = mapper.get_score("functional", blockage_defect)
    if bl_score is None:
        bl_score = 50.0 if "no defect" in blockage_defect.lower() else 0.0
    
    cd_score = mapper.get_score("concrete_damage", concrete_defect)
    if cd_score is None:
        cd_score = mapper.get_score("appearance", concrete_defect)
    if cd_score is None:
        cd_score = 50.0 if "no defect" in concrete_defect.lower() else 0.0
    
    aci = bl_score + cd_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "blockage": bl_score,
            "concrete_damage": cd_score
        },
        formula="BL + CD"
    )


def calculate_hump(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Road Hump.
    
    Formula: ACI = Structural_Score + Appearance_Score
    S max = 50, A max = 50
    """
    mapper = DefectMapper("HUMP")
    
    structural_defect = defects.structural_defect or defects.functional_defect or "No Defect Found"
    appearance_defect = defects.appearance_defect or "No Defect Found"
    
    s_score = mapper.get_score("structural", structural_defect)
    if s_score is None:
        s_score = mapper.get_score("functional", structural_defect)
    if s_score is None:
        s_score = 50.0 if "no defect" in structural_defect.lower() else 0.0
    
    a_score = mapper.get_score("appearance", appearance_defect)
    if a_score is None:
        a_score = 50.0 if "no defect" in appearance_defect.lower() else 0.0
    
    aci = s_score + a_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "structural": s_score,
            "appearance": a_score
        },
        formula="S + A"
    )


def calculate_bench_cycle_rack(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI for Bench or Cycle Rack.
    
    Formula: ACI = Structural_Score + Appearance_Score
    S max = 60, A max = 40
    """
    mapper = DefectMapper(asset_type)
    
    structural_defect = defects.structural_defect or defects.functional_defect or "No Defect Found"
    appearance_defect = defects.appearance_defect or "No Defect Found"
    
    s_score = mapper.get_score("structural", structural_defect)
    if s_score is None:
        s_score = mapper.get_score("functional", structural_defect)
    if s_score is None:
        s_score = 60.0 if "no defect" in structural_defect.lower() else 0.0
    
    a_score = mapper.get_score("appearance", appearance_defect)
    if a_score is None:
        a_score = 40.0 if "no defect" in appearance_defect.lower() else 0.0
    
    aci = s_score + a_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "structural": s_score,
            "appearance": a_score
        },
        formula="S + A"
    )


def calculate(asset_type: str, defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for any simple asset type.
    
    Dispatches to the appropriate calculation function based on asset type.
    
    Args:
        asset_type: Asset type key
        defects: DefectInput with appropriate defect fields
        
    Returns:
        ACIResult
    """
    asset_upper = asset_type.upper().replace(" ", "_")
    
    if asset_upper == "DRAINAGE_POINT":
        return calculate_drainage_point(defects)
    elif asset_upper == "HUMP":
        return calculate_hump(defects)
    elif asset_upper in ["BENCH", "CYCLE_RACK"]:
        return calculate_bench_cycle_rack(asset_upper, defects)
    elif asset_upper in FUNCTIONAL_ONLY_ASSETS:
        return calculate_functional_only(asset_upper, defects)
    else:
        return calculate_simple_fa(asset_upper, defects)
