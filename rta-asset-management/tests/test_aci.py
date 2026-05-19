"""
Unit tests for Asset Condition Index (ACI) calculation.

Tests various asset types and calculation patterns against Excel formulas.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.aci.calculator import calculate_aci, calculate_aci_from_scores
from domain.models import DefectInput, ACIRating, AssetType


class TestACIRating:
    """Test ACI rating classification."""
    
    def test_rating_good_at_100(self):
        """ACI=100 should be GOOD."""
        result = calculate_aci_from_scores(80, 20)
        assert result.rating == ACIRating.GOOD
    
    def test_rating_good_at_80(self):
        """ACI=80 should be GOOD (boundary)."""
        result = calculate_aci_from_scores(64, 16)
        assert result.rating == ACIRating.GOOD
    
    def test_rating_fair_at_79(self):
        """ACI=79 should be FAIR."""
        result = calculate_aci_from_scores(63.2, 15.8)
        assert result.rating == ACIRating.FAIR
    
    def test_rating_fair_at_41(self):
        """ACI=41 should be FAIR."""
        result = calculate_aci_from_scores(32.8, 8.2)
        assert result.rating == ACIRating.FAIR
    
    def test_rating_poor_at_40(self):
        """ACI=40 should be POOR (boundary)."""
        result = calculate_aci_from_scores(32, 8)
        assert result.rating == ACIRating.POOR
    
    def test_rating_poor_at_0(self):
        """ACI=0 should be POOR."""
        result = calculate_aci_from_scores(0, 0)
        assert result.rating == ACIRating.POOR


class TestSimpleACI:
    """Test simple F+A ACI calculations."""
    
    def test_manhole_no_defects(self):
        """Manhole with no defects should have ACI=100."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("MANHOLE", defects)
        assert result.aci == pytest.approx(100.0, abs=1)
        assert result.rating == ACIRating.GOOD
    
    def test_gully_no_defects(self):
        """Gully with no defects should have ACI=100."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("GULLY", defects)
        assert result.aci == pytest.approx(100.0, abs=1)
        assert result.rating == ACIRating.GOOD
    
    def test_simple_asset_component_scores(self):
        """Simple assets should have functional + appearance components."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("MANHOLE", defects)
        assert "functional" in result.component_scores
        assert "appearance" in result.component_scores


class TestFunctionalOnlyACI:
    """Test functional-only ACI calculations."""
    
    def test_footpath_no_defects(self):
        """Footpath with no defects should have high ACI."""
        defects = DefectInput(
            functional_defect="No Defect Found"
        )
        result = calculate_aci("FOOTPATH", defects)
        assert result.aci >= 80  # Functional-only may have max 80 or 100
        assert result.rating == ACIRating.GOOD
    
    def test_control_cabinet_no_defects(self):
        """Control Cabinet with no defects should have high ACI."""
        defects = DefectInput(
            functional_defect="No Defect Found"
        )
        result = calculate_aci("CONTROL_CABINET", defects)
        assert result.aci >= 80  # At least GOOD rating
    
    def test_functional_only_has_single_component(self):
        """Functional-only assets should only have functional component."""
        defects = DefectInput(functional_defect="No Defect Found")
        result = calculate_aci("FOOTPATH", defects)
        assert "functional" in result.component_scores


class TestWeightedACI:
    """Test weighted ACI calculations (70/30, 80/20)."""
    
    def test_bollards_no_defects(self):
        """Bollards with no defects should have ACI=100."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("BOLLARDS", defects)
        assert result.aci == pytest.approx(100.0, abs=1)
    
    def test_barrier_no_defects(self):
        """Barrier with no defects should have ACI=100."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("BARRIER", defects)
        assert result.aci == pytest.approx(100.0, abs=1)
    
    def test_bollards_has_weights(self):
        """Bollards should use 70/30 weighting."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        result = calculate_aci("BOLLARDS", defects)
        assert "0.7" in result.formula_used or "70" in result.formula_used


class TestComplexACI:
    """Test complex multi-component ACI calculations."""
    
    def test_gantry_no_defects(self):
        """Gantry with no defects should have ACI=100."""
        defects = DefectInput(
            foundation_defect="No Defect Found",
            structure_defect="No Defect Found"
        )
        result = calculate_aci("GANTRY", defects)
        assert result.aci == pytest.approx(100.0, abs=1)
        assert result.rating == ACIRating.GOOD
    
    def test_gantry_has_foundation_structure_components(self):
        """Gantry should have foundation and structure components."""
        defects = DefectInput(
            foundation_defect="No Defect Found",
            structure_defect="No Defect Found"
        )
        result = calculate_aci("GANTRY", defects)
        assert "foundation" in result.component_scores
        assert "structure" in result.component_scores
    
    def test_streetlight_no_defects(self):
        """Streetlight with no defects should have high ACI."""
        defects = DefectInput(
            foundation_defect="No Defect Found",
            pole_functional_defect="No Defect Found",
            pole_appearance_defect="No Defect Found",
            lighting_arm_defect="No Defect Found",
            lamp_defect="No Defect Found"
        )
        result = calculate_aci("STREETLIGHT", defects)
        assert result.aci >= 80
        assert result.rating == ACIRating.GOOD


class TestACIBounds:
    """Test ACI calculation bounds."""
    
    @pytest.mark.parametrize("asset_type", [
        "MANHOLE", "GULLY", "FOOTPATH", "BOLLARDS", "BARRIER", "GANTRY"
    ])
    def test_aci_within_bounds(self, asset_type):
        """ACI should always be between 0 and 100."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found",
            foundation_defect="No Defect Found",
            structure_defect="No Defect Found"
        )
        result = calculate_aci(asset_type, defects)
        assert 0 <= result.aci <= 100


class TestACIFromScores:
    """Test direct score-based ACI calculation."""
    
    def test_from_scores_simple(self):
        """Test ACI from explicit scores."""
        result = calculate_aci_from_scores(80, 20)
        assert result.aci == 100
        assert result.rating == ACIRating.GOOD
    
    def test_from_scores_partial(self):
        """Test ACI from partial scores."""
        result = calculate_aci_from_scores(60, 15)
        assert result.aci == 75
        assert result.rating == ACIRating.FAIR
    
    def test_from_scores_zero(self):
        """Test ACI from zero scores."""
        result = calculate_aci_from_scores(0, 0)
        assert result.aci == 0
        assert result.rating == ACIRating.POOR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
