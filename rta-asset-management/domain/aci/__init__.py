"""
Asset Condition Index (ACI) calculation modules.

ACI is a composite score (0-100) measuring asset condition from defect observations.

Modules:
- calculator: Main entry point and dispatcher
- simple: F+A and F-only asset calculations
- weighted: 70/30 and 80/20 weighted calculations
- complex: Multi-component assets (gantry, traffic signal, etc.)
- defect_mapper: Defect text to numeric score mapping
"""

from domain.aci.calculator import calculate_aci
from domain.aci.defect_mapper import DefectMapper, get_defect_score

__all__ = [
    "calculate_aci",
    "DefectMapper",
    "get_defect_score",
]
