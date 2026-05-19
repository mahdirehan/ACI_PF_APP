"""
Defect-to-score mapping module.

Implements VLOOKUP-like behavior from Excel ACI sheets,
mapping defect description text to numeric scores.
"""

from typing import Optional
from domain.lookups.loader import load_defect_mapping


class DefectMapper:
    """
    Maps defect descriptions to numeric scores for ACI calculation.
    
    Implements the VLOOKUP logic from Excel ACI sheets where
    defect dropdown selections map to predefined scores.
    """
    
    def __init__(self, asset_type: str):
        """
        Initialize mapper for an asset type.
        
        Args:
            asset_type: Asset type key (e.g., "MANHOLE", "GANTRY")
        """
        self.asset_type = asset_type.upper().replace(" ", "_")
        self._mapping = load_defect_mapping(self.asset_type)
        self._score_cache: dict[tuple[str, str], Optional[float]] = {}
    
    @property
    def is_loaded(self) -> bool:
        """Check if mapping data was successfully loaded."""
        return self._mapping is not None
    
    @property
    def aci_formula(self) -> str:
        """Get the ACI formula for this asset type."""
        if self._mapping:
            return self._mapping.get("aci_formula", "F + A")
        return "F + A"
    
    @property
    def weights(self) -> dict[str, float]:
        """Get the component weights for this asset type."""
        if self._mapping:
            return self._mapping.get("weights", {"functional": 0.8, "appearance": 0.2})
        return {"functional": 0.8, "appearance": 0.2}
    
    @property
    def categories(self) -> list[str]:
        """Get list of defect categories for this asset type."""
        if self._mapping:
            return [c.get("name", "") for c in self._mapping.get("defect_categories", [])]
        return []
    
    def get_score(
        self,
        category: str,
        defect_text: str,
        default: Optional[float] = None
    ) -> Optional[float]:
        """
        Look up score for a defect description.
        
        Args:
            category: Defect category (e.g., "functional", "appearance")
            defect_text: Defect description text
            default: Default value if not found
            
        Returns:
            Numeric score or default value
        """
        cache_key = (category.lower(), defect_text.strip().lower())
        if cache_key in self._score_cache:
            return self._score_cache[cache_key]
        
        score = self._lookup_score(category, defect_text)
        if score is None:
            score = default
        
        self._score_cache[cache_key] = score
        return score
    
    def _lookup_score(self, category: str, defect_text: str) -> Optional[float]:
        """Internal score lookup logic."""
        if not self._mapping:
            return None
        
        categories = self._mapping.get("defect_categories", [])
        defect_text_lower = defect_text.strip().lower()
        
        for cat in categories:
            if cat.get("name", "").lower() != category.lower():
                continue
            
            defects = cat.get("defects", [])
            for defect in defects:
                text = defect.get("text", "").strip().lower()
                if text == defect_text_lower:
                    score = defect.get("score")
                    if score is not None:
                        return float(score)
            
            if "no defect" in defect_text_lower or defect_text_lower == "":
                max_score = cat.get("max_score")
                if max_score is not None:
                    return float(max_score)
                for defect in defects:
                    if "no defect" in defect.get("text", "").lower():
                        score = defect.get("score")
                        if score is not None:
                            return float(score)
        
        return None
    
    def get_max_score(self, category: str) -> float:
        """
        Get the maximum possible score for a category.
        
        Args:
            category: Defect category
            
        Returns:
            Maximum score (usually 80 for functional, 20 for appearance)
        """
        if not self._mapping:
            if category.lower() == "functional":
                return 80.0
            return 20.0
        
        categories = self._mapping.get("defect_categories", [])
        for cat in categories:
            if cat.get("name", "").lower() == category.lower():
                max_score = cat.get("max_score")
                if max_score is not None:
                    return float(max_score)
        
        if category.lower() == "functional":
            return 80.0
        return 20.0
    
    def get_all_defects(self, category: str) -> list[dict]:
        """
        Get all defect options for a category.
        
        Args:
            category: Defect category
            
        Returns:
            List of {text, score} dicts
        """
        if not self._mapping:
            return []
        
        categories = self._mapping.get("defect_categories", [])
        for cat in categories:
            if cat.get("name", "").lower() == category.lower():
                return cat.get("defects", [])
        
        return []


def get_defect_score(
    asset_type: str,
    category: str,
    defect_text: str,
    default: Optional[float] = None
) -> Optional[float]:
    """
    Convenience function to look up a defect score.
    
    Args:
        asset_type: Asset type key
        category: Defect category
        defect_text: Defect description
        default: Default value if not found
        
    Returns:
        Numeric score or default
    """
    mapper = DefectMapper(asset_type)
    return mapper.get_score(category, defect_text, default)


def get_functional_score(asset_type: str, defect_text: str) -> float:
    """Get functional defect score, defaulting to max (80) for no defect."""
    mapper = DefectMapper(asset_type)
    score = mapper.get_score("functional", defect_text)
    if score is None:
        if "no defect" in defect_text.lower() or not defect_text.strip():
            return mapper.get_max_score("functional")
        return 0.0
    return score


def get_appearance_score(asset_type: str, defect_text: str) -> float:
    """Get appearance defect score, defaulting to max (20) for no defect."""
    mapper = DefectMapper(asset_type)
    score = mapper.get_score("appearance", defect_text)
    if score is None:
        if "no defect" in defect_text.lower() or not defect_text.strip():
            return mapper.get_max_score("appearance")
        return 0.0
    return score
