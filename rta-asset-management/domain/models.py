"""
Data models for RTA Asset Management calculation engine.

All models use Pydantic for validation, serialization, and OpenAPI schema generation.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field


class ACIRating(str, Enum):
    """Asset Condition Index rating classification."""
    GOOD = "GOOD"   # ACI >= 80
    FAIR = "FAIR"   # 40 < ACI < 80
    POOR = "POOR"   # ACI <= 40


class AssetCategory(str, Enum):
    """Categories of assets based on ACI calculation method."""
    SIMPLE_F_A = "simple_f_a"           # F + A = 100 (functional 80 + appearance 20)
    FUNCTIONAL_ONLY = "functional_only"  # F = 100
    WEIGHTED_70_30 = "weighted_70_30"    # F*0.7 + A*0.3
    WEIGHTED_80_20 = "weighted_80_20"    # F*0.8 + A*0.2
    COMPLEX = "complex"                  # Multi-component formulas


class AssetType(str, Enum):
    """All supported asset types in the RTA system."""
    # Simple F+A assets (Functional 80 + Appearance 20)
    MANHOLE = "MANHOLE"
    GULLY = "GULLY"
    CURBSTONE = "CURBSTONE"
    GUARDRAIL = "GUARDRAIL"
    FENCE = "FENCE"
    HUMP = "HUMP"
    BENCH = "BENCH"
    CYCLE_RACK = "CYCLE_RACK"
    WOODEN_DECK = "WOODEN_DECK"
    JOGGING_TRACK = "JOGGING_TRACK"
    ROAD_SIGN_POLE = "ROAD_SIGN_POLE"
    DRAINAGE_POINT = "DRAINAGE_POINT"
    CRASH_CUSHION = "CRASH_CUSHION"
    
    # Functional-only assets (F = 100)
    ROAD_STUD = "ROAD_STUD"
    FOOTPATH = "FOOTPATH"
    CAMEL_GRID = "CAMEL_GRID"
    CONTROL_CABINET = "CONTROL_CABINET"
    ROADSIDE_CAMERA = "ROADSIDE_CAMERA"
    DECORATIVE_FURNITURE = "DECORATIVE_FURNITURE"
    LANDSCAPE = "LANDSCAPE"
    PARKING = "PARKING"
    LABAY = "LABAY"
    SHOULDER = "SHOULDER"
    ISLAND = "ISLAND"
    
    # Weighted 70/30 assets
    BOLLARDS = "BOLLARDS"
    ROAD_MARKING = "ROAD_MARKING"
    ROAD_MARKING_SYMBOL = "ROAD_MARKING_SYMBOL"
    
    # Weighted 80/20 assets
    BARRIER = "BARRIER"
    
    # Complex multi-component assets
    GANTRY = "GANTRY"
    TRAFFIC_SIGNAL = "TRAFFIC_SIGNAL"
    STREETLIGHT = "STREETLIGHT"
    PERGOLA = "PERGOLA"
    PUBLIC_SHED = "PUBLIC_SHED"
    PARKING_TENTS = "PARKING_TENTS"
    PEDESTRIAN_CROSSING = "PEDESTRIAN_CROSSING"
    ROAD_SIGN_FACE_AND_POLE = "ROAD_SIGN_FACE_AND_POLE"


# Asset type to category mapping
ASSET_CATEGORIES: dict[AssetType, AssetCategory] = {
    # Simple F+A
    AssetType.MANHOLE: AssetCategory.SIMPLE_F_A,
    AssetType.GULLY: AssetCategory.SIMPLE_F_A,
    AssetType.CURBSTONE: AssetCategory.SIMPLE_F_A,
    AssetType.GUARDRAIL: AssetCategory.SIMPLE_F_A,
    AssetType.FENCE: AssetCategory.SIMPLE_F_A,
    AssetType.HUMP: AssetCategory.SIMPLE_F_A,
    AssetType.BENCH: AssetCategory.SIMPLE_F_A,
    AssetType.CYCLE_RACK: AssetCategory.SIMPLE_F_A,
    AssetType.WOODEN_DECK: AssetCategory.SIMPLE_F_A,
    AssetType.JOGGING_TRACK: AssetCategory.SIMPLE_F_A,
    AssetType.ROAD_SIGN_POLE: AssetCategory.SIMPLE_F_A,
    AssetType.DRAINAGE_POINT: AssetCategory.SIMPLE_F_A,
    AssetType.CRASH_CUSHION: AssetCategory.SIMPLE_F_A,
    
    # Functional only
    AssetType.ROAD_STUD: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.FOOTPATH: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.CAMEL_GRID: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.CONTROL_CABINET: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.ROADSIDE_CAMERA: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.DECORATIVE_FURNITURE: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.LANDSCAPE: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.PARKING: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.LABAY: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.SHOULDER: AssetCategory.FUNCTIONAL_ONLY,
    AssetType.ISLAND: AssetCategory.FUNCTIONAL_ONLY,
    
    # Weighted 70/30
    AssetType.BOLLARDS: AssetCategory.WEIGHTED_70_30,
    AssetType.ROAD_MARKING: AssetCategory.WEIGHTED_70_30,
    AssetType.ROAD_MARKING_SYMBOL: AssetCategory.WEIGHTED_70_30,
    
    # Weighted 80/20
    AssetType.BARRIER: AssetCategory.WEIGHTED_80_20,
    
    # Complex
    AssetType.GANTRY: AssetCategory.COMPLEX,
    AssetType.TRAFFIC_SIGNAL: AssetCategory.COMPLEX,
    AssetType.STREETLIGHT: AssetCategory.COMPLEX,
    AssetType.PERGOLA: AssetCategory.COMPLEX,
    AssetType.PUBLIC_SHED: AssetCategory.COMPLEX,
    AssetType.PARKING_TENTS: AssetCategory.COMPLEX,
    AssetType.PEDESTRIAN_CROSSING: AssetCategory.COMPLEX,
    AssetType.ROAD_SIGN_FACE_AND_POLE: AssetCategory.COMPLEX,
}


class DefectInput(BaseModel):
    """Input model for defect descriptions used in ACI calculation."""
    
    # Common defect fields
    functional_defect: Optional[str] = Field(
        default=None, 
        description="Functional defect description from dropdown"
    )
    appearance_defect: Optional[str] = Field(
        default=None,
        description="Appearance defect description from dropdown"
    )
    
    # Complex asset fields (foundation/structure)
    foundation_defect: Optional[str] = Field(
        default=None,
        description="Foundation defect (for gantry, traffic signal, streetlight, etc.)"
    )
    structure_defect: Optional[str] = Field(
        default=None,
        description="Structure defect (for gantry)"
    )
    
    # Pole-based assets
    pole_functional_defect: Optional[str] = Field(
        default=None,
        description="Pole functional defect (traffic signal, streetlight)"
    )
    pole_appearance_defect: Optional[str] = Field(
        default=None,
        description="Pole appearance defect"
    )
    
    # Traffic signal / streetlight specific
    signal_head_defect: Optional[str] = Field(
        default=None,
        description="Signal head/light defect"
    )
    lighting_arm_defect: Optional[str] = Field(
        default=None,
        description="Lighting arm defect (streetlight)"
    )
    lamp_defect: Optional[str] = Field(
        default=None,
        description="Lamp defect (streetlight)"
    )
    
    # Structure-based assets (pergola, shed, tent)
    column_functional_defect: Optional[str] = Field(
        default=None,
        description="Column functionality defect"
    )
    column_appearance_defect: Optional[str] = Field(
        default=None,
        description="Column appearance defect"
    )
    roof_defect: Optional[str] = Field(
        default=None,
        description="Roof defect (pergola, shed, tent)"
    )
    
    # Road marking / pedestrian crossing
    visibility_defect: Optional[str] = Field(
        default=None,
        description="Visibility defect (road marking, pedestrian crossing)"
    )
    presence_defect: Optional[str] = Field(
        default=None,
        description="Presence defect (road marking fading)"
    )
    structural_defect: Optional[str] = Field(
        default=None,
        description="Structural defect (pedestrian crossing)"
    )
    
    # Road sign specific
    sign_face_visibility_defect: Optional[str] = Field(
        default=None,
        description="Sign face visibility defect"
    )
    sign_face_presence_defect: Optional[str] = Field(
        default=None,
        description="Sign face presence defect"
    )
    
    # Retroreflectivity measurement (for road marking, signs)
    retroreflectivity_value: Optional[float] = Field(
        default=None,
        ge=0,
        description="Measured retroreflectivity (RL) value"
    )
    observation_angle: Optional[str] = Field(
        default=None,
        description="Observation angle for retroreflectivity"
    )
    entrance_angle: Optional[str] = Field(
        default=None,
        description="Entrance angle for retroreflectivity"
    )
    color: Optional[str] = Field(
        default=None,
        description="Sign/marking color for threshold lookup"
    )
    
    # Drainage point specific
    blockage_defect: Optional[str] = Field(
        default=None,
        description="Blockage defect (drainage point)"
    )
    concrete_damage_defect: Optional[str] = Field(
        default=None,
        description="Concrete damage defect (drainage point)"
    )

    model_config = ConfigDict(extra="allow")


class ACIResult(BaseModel):
    """Result of Asset Condition Index calculation."""
    
    aci: float = Field(
        ge=0, 
        le=100,
        description="Asset Condition Index score (0-100)"
    )
    rating: ACIRating = Field(
        description="Rating classification (GOOD/FAIR/POOR)"
    )
    component_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual component scores (e.g., functional, appearance)"
    )
    formula_used: str = Field(
        default="",
        description="Formula used for this calculation"
    )
    
    @classmethod
    def from_aci(cls, aci: float, component_scores: dict[str, float] = None, formula: str = "") -> "ACIResult":
        """Create ACIResult from ACI value, automatically determining rating."""
        rating = get_aci_rating(aci)
        return cls(
            aci=round(aci, 2),
            rating=rating,
            component_scores=component_scores or {},
            formula_used=formula
        )


class PFResult(BaseModel):
    """Result of Priority Factor calculation."""
    
    pf: float = Field(
        description="Priority Factor score"
    )
    cf: float = Field(
        ge=0,
        le=100,
        description="Condition Factor (0-100)"
    )
    rf: float = Field(
        ge=10,
        le=100,
        description="Risk Factor (10-100)"
    )
    flf: float = Field(
        ge=0,
        le=100,
        description="Functional Life Factor (0-100)"
    )
    aci: float = Field(
        ge=0,
        le=100,
        description="Source ACI value"
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {"cf": 0.6, "rf": 0.2, "flf": 0.2},
        description="Weights used for PF calculation"
    )


@dataclass
class DeteriorationCurve:
    """Parameters for FLF deterioration equation.
    
    Equation form: ConsumedLife = (ACI - intercept) / slope
    FLF = (ConsumedLife / total_life) * 100, clamped to 0-100
    """
    intercept: float
    slope: float
    total_life: float
    name: str = ""
    
    def calculate_consumed_life(self, aci: float) -> float:
        """Calculate consumed life years from ACI."""
        return (aci - self.intercept) / self.slope
    
    def calculate_flf(self, aci: float) -> float:
        """Calculate FLF percentage from ACI."""
        if aci == 0:
            return 100.0
        if aci >= 80:
            return 0.0
        consumed = self.calculate_consumed_life(aci)
        flf = (consumed / self.total_life) * 100
        return max(0.0, min(100.0, flf))


def get_aci_rating(aci: float) -> ACIRating:
    """
    Determine ACI rating from score.
    
    Excel formula: =IF(AND(ACI>=80,ACI<=100),"GOOD",IF(AND(ACI>40,ACI<80),"FAIR","POOR"))
    
    Args:
        aci: Asset Condition Index score (0-100)
        
    Returns:
        ACIRating enum value
    """
    if aci >= 80:
        return ACIRating.GOOD
    elif aci > 40:
        return ACIRating.FAIR
    else:
        return ACIRating.POOR


def get_asset_category(asset_type: AssetType) -> AssetCategory:
    """Get the calculation category for an asset type."""
    return ASSET_CATEGORIES.get(asset_type, AssetCategory.SIMPLE_F_A)
