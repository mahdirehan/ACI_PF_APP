"""
RTA Asset Management Domain Package

Pure Python calculation engine for Asset Condition Index (ACI) and Priority Factor (PF).
Designed for reuse in FastAPI backend, ArcGIS Pro toolbox, and testing.
"""

from domain.models import (
    ACIRating,
    AssetType,
    AssetCategory,
    DefectInput,
    ACIResult,
    PFResult,
    DeteriorationCurve,
)

__all__ = [
    "ACIRating",
    "AssetType", 
    "AssetCategory",
    "DefectInput",
    "ACIResult",
    "PFResult",
    "DeteriorationCurve",
]

__version__ = "0.1.0"
