"""
Complex ACI calculator for multi-component assets.

Handles assets with 3+ components requiring weighted aggregation:
- Gantry: 0.4*Foundation + 0.3*SignScore + 0.3*(V+P)
- Traffic Signal: 0.2*Foundation + 0.2*(PoleFunctional+PoleAppearance) + 0.6*SignalHead
- Streetlight: 0.2*Foundation + 0.2*(PoleFunctional+PoleAppearance) + 0.3*LightingArm + 0.3*Lamp
- Pergola/Public Shed/Parking Tent: 0.4*Foundation + 0.3*(ColumnFunc+ColumnApp) + 0.3*Roof
- Pedestrian Crossing: 0.5*Structural + 0.5*(V+P)
- Road Sign Face+Pole: 0.9*FaceACI + 0.1*PoleACI
"""

from typing import Optional
from domain.models import DefectInput, ACIResult, get_aci_rating
from domain.aci.defect_mapper import DefectMapper


COMPLEX_ASSETS = [
    "GANTRY", "TRAFFIC_SIGNAL", "TRAFIC_SIGNAL", "STREETLIGHT",
    "PERGOLA", "PUBLIC_SHED", "PARKING_TENTS",
    "PEDESTRIAN_CROSSING", "ROAD_SIGN_FACE_AND_POLE"
]


def calculate_gantry(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Road Gantry.
    
    Formula: ACI = 0.6*Foundation + 0.4*Structure
    (Simplified from full: 0.4*Foundation + 0.3*SignScore + 0.3*(V+P))
    
    The MASTER_EXCEL uses Foundation/Structure split with 60/40 weighting.
    """
    mapper = DefectMapper("GANTRY")
    
    foundation_defect = defects.foundation_defect or "No Defect Found"
    structure_defect = defects.structure_defect or "No Defect Found"
    
    f_score = mapper.get_score("foundation", foundation_defect)
    if f_score is None:
        f_score = 60.0 if "no defect" in foundation_defect.lower() else _infer_score(foundation_defect, 60)
    
    s_score = mapper.get_score("structure", structure_defect)
    if s_score is None:
        s_score = 40.0 if "no defect" in structure_defect.lower() else _infer_score(structure_defect, 40)
    
    aci = f_score + s_score
    aci = max(0, min(100, aci))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "foundation": round(f_score, 2),
            "structure": round(s_score, 2)
        },
        formula="Foundation + Structure (60/40)"
    )


def calculate_traffic_signal(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Traffic Signal.
    
    Formula: ACI = 0.2*Foundation + 0.2*(PoleFunctional+PoleAppearance) + 0.6*SignalHead
    """
    mapper = DefectMapper("TRAFIC_SIGNAL")
    
    foundation_defect = defects.foundation_defect or "No Defect Found"
    pole_func_defect = defects.pole_functional_defect or defects.functional_defect or "No Defect Found"
    pole_app_defect = defects.pole_appearance_defect or defects.appearance_defect or "No Defect Found"
    signal_defect = defects.signal_head_defect or "No Defect Found"
    
    f_score = _get_component_score(mapper, "foundation", foundation_defect, 100)
    pf_score = _get_component_score(mapper, "pole_functional", pole_func_defect, 70)
    pa_score = _get_component_score(mapper, "pole_appearance", pole_app_defect, 30)
    sh_score = _get_component_score(mapper, "signal_head", signal_defect, 100)
    
    aci = 0.2 * f_score + 0.2 * (pf_score + pa_score) / 100 * 100 + 0.6 * sh_score
    aci = max(0, min(100, round(aci, 0)))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "foundation": round(f_score, 2),
            "pole_functional": round(pf_score, 2),
            "pole_appearance": round(pa_score, 2),
            "signal_head": round(sh_score, 2)
        },
        formula="0.2*F + 0.2*(PF+PA) + 0.6*SH"
    )


def calculate_streetlight(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Streetlight.
    
    Formula: ACI = 0.2*Foundation + 0.2*(PoleFunctional+PoleAppearance) + 0.3*LightingArm + 0.3*Lamp
    """
    mapper = DefectMapper("STREETLIGHT")
    
    foundation_defect = defects.foundation_defect or "No Defect Found"
    pole_func_defect = defects.pole_functional_defect or "No Defect Found"
    pole_app_defect = defects.pole_appearance_defect or "No Defect Found"
    arm_defect = defects.lighting_arm_defect or "No Defect Found"
    lamp_defect = defects.lamp_defect or "No Defect Found"
    
    f_score = _get_component_score(mapper, "foundation", foundation_defect, 100)
    pf_score = _get_component_score(mapper, "pole_functional", pole_func_defect, 70)
    pa_score = _get_component_score(mapper, "pole_appearance", pole_app_defect, 30)
    arm_score = _get_component_score(mapper, "lighting_arm", arm_defect, 100)
    lamp_score = _get_component_score(mapper, "lamp", lamp_defect, 100)
    
    pole_combined = (pf_score + pa_score)
    aci = 0.2 * f_score + 0.2 * pole_combined + 0.3 * arm_score + 0.3 * lamp_score
    aci = max(0, min(100, round(aci, 0)))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "foundation": round(f_score, 2),
            "pole_functional": round(pf_score, 2),
            "pole_appearance": round(pa_score, 2),
            "lighting_arm": round(arm_score, 2),
            "lamp": round(lamp_score, 2)
        },
        formula="0.2*F + 0.2*(PF+PA) + 0.3*Arm + 0.3*Lamp"
    )


def calculate_pergola_shed_tent(
    asset_type: str,
    defects: DefectInput
) -> ACIResult:
    """
    Calculate ACI for Pergola, Public Shed, or Parking Tent.
    
    Formula: ACI = 0.4*Foundation + 0.3*(ColumnFunc+ColumnApp) + 0.3*Roof
    """
    mapper = DefectMapper(asset_type)
    
    foundation_defect = defects.foundation_defect or "No Defect Found"
    col_func_defect = defects.column_functional_defect or defects.functional_defect or "No Defect Found"
    col_app_defect = defects.column_appearance_defect or defects.appearance_defect or "No Defect Found"
    roof_defect = defects.roof_defect or "No Defect Found"
    
    f_score = _get_component_score(mapper, "foundation", foundation_defect, 100)
    cf_score = _get_component_score(mapper, "column_functional", col_func_defect, 50)
    ca_score = _get_component_score(mapper, "column_appearance", col_app_defect, 50)
    r_score = _get_component_score(mapper, "roof", roof_defect, 100)
    
    column_combined = cf_score + ca_score
    aci = 0.4 * f_score + 0.3 * column_combined + 0.3 * r_score
    aci = max(0, min(100, round(aci, 0)))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "foundation": round(f_score, 2),
            "column_functional": round(cf_score, 2),
            "column_appearance": round(ca_score, 2),
            "roof": round(r_score, 2)
        },
        formula="0.4*F + 0.3*(CF+CA) + 0.3*R"
    )


def calculate_pedestrian_crossing(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Pedestrian Crossing.
    
    Formula: ACI = 0.5*Structural + 0.5*(Visibility+Presence)
    """
    mapper = DefectMapper("PEDESTRIAN_CROSSING")
    
    structural_defect = defects.structural_defect or defects.functional_defect or "No Defect Found"
    visibility_defect = defects.visibility_defect or "No Defect Found"
    presence_defect = defects.presence_defect or defects.appearance_defect or "No Defect Found"
    
    s_score = _get_component_score(mapper, "structural", structural_defect, 100)
    v_score = _get_component_score(mapper, "visibility", visibility_defect, 70)
    p_score = _get_component_score(mapper, "presence", presence_defect, 30)
    
    vp_combined = v_score + p_score
    aci = 0.5 * s_score + 0.5 * vp_combined
    aci = max(0, min(100, round(aci, 0)))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "structural": round(s_score, 2),
            "visibility": round(v_score, 2),
            "presence": round(p_score, 2)
        },
        formula="0.5*S + 0.5*(V+P)"
    )


def calculate_road_sign_face_pole(defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for Road Sign (Face + Pole combined).
    
    Formula: ACI = 0.9*FaceACI + 0.1*PoleACI
    """
    mapper_face = DefectMapper("ROAD_SIGN_FACE_AND_POLE")
    mapper_pole = DefectMapper("ROAD_SIGN_POLE")
    
    visibility_defect = defects.sign_face_visibility_defect or defects.visibility_defect or "No Defect Found"
    presence_defect = defects.sign_face_presence_defect or defects.presence_defect or "No Defect Found"
    pole_func_defect = defects.pole_functional_defect or defects.functional_defect or "No Defect Found"
    pole_app_defect = defects.pole_appearance_defect or defects.appearance_defect or "No Defect Found"
    
    v_score = _get_component_score(mapper_face, "visibility", visibility_defect, 50)
    p_score = _get_component_score(mapper_face, "presence", presence_defect, 50)
    face_aci = v_score + p_score
    
    pf_score = _get_component_score(mapper_pole, "functional", pole_func_defect, 80)
    pa_score = _get_component_score(mapper_pole, "appearance", pole_app_defect, 20)
    pole_aci = pf_score + pa_score
    
    aci = 0.9 * face_aci + 0.1 * pole_aci
    aci = max(0, min(100, round(aci, 0)))
    
    return ACIResult.from_aci(
        aci=aci,
        component_scores={
            "face_visibility": round(v_score, 2),
            "face_presence": round(p_score, 2),
            "face_aci": round(face_aci, 2),
            "pole_functional": round(pf_score, 2),
            "pole_appearance": round(pa_score, 2),
            "pole_aci": round(pole_aci, 2)
        },
        formula="0.9*FaceACI + 0.1*PoleACI"
    )


def _get_component_score(
    mapper: DefectMapper,
    category: str,
    defect_text: str,
    max_score: float
) -> float:
    """
    Get component score from mapper with fallback to inference.
    """
    score = mapper.get_score(category, defect_text)
    if score is not None:
        return score
    
    if "no defect" in defect_text.lower():
        return max_score
    
    return _infer_score(defect_text, max_score)


def _infer_score(defect_text: str, max_score: float) -> float:
    """
    Infer a score from defect description when lookup fails.
    
    Uses keyword matching as fallback.
    """
    text_lower = defect_text.lower()
    
    if "no defect" in text_lower:
        return max_score
    elif "minor" in text_lower or "5%" in text_lower:
        return max_score * 0.9
    elif "10%" in text_lower:
        return max_score * 0.8
    elif "20%" in text_lower or "moderate" in text_lower:
        return max_score * 0.7
    elif "30%" in text_lower:
        return max_score * 0.6
    elif "major" in text_lower or "40%" in text_lower:
        return max_score * 0.5
    elif "severe" in text_lower or "50%" in text_lower:
        return max_score * 0.4
    elif "critical" in text_lower or "broken" in text_lower:
        return max_score * 0.2
    elif "failed" in text_lower or "missing" in text_lower:
        return 0.0
    
    return max_score * 0.5


def calculate(asset_type: str, defects: DefectInput) -> ACIResult:
    """
    Calculate ACI for any complex asset type.
    
    Dispatches to the appropriate calculation function based on asset type.
    
    Args:
        asset_type: Asset type key
        defects: DefectInput with appropriate defect fields
        
    Returns:
        ACIResult
    """
    asset_upper = asset_type.upper().replace(" ", "_")
    
    if asset_upper in ["GANTRY", "ROAD_GANTRY"]:
        return calculate_gantry(defects)
    elif asset_upper in ["TRAFFIC_SIGNAL", "TRAFIC_SIGNAL"]:
        return calculate_traffic_signal(defects)
    elif asset_upper == "STREETLIGHT":
        return calculate_streetlight(defects)
    elif asset_upper in ["PERGOLA", "PUBLIC_SHED", "PARKING_TENTS"]:
        return calculate_pergola_shed_tent(asset_upper, defects)
    elif asset_upper == "PEDESTRIAN_CROSSING":
        return calculate_pedestrian_crossing(defects)
    elif asset_upper == "ROAD_SIGN_FACE_AND_POLE":
        return calculate_road_sign_face_pole(defects)
    else:
        raise ValueError(f"Unknown complex asset type: {asset_type}")
