"""
Integration tests for Priority Factor (PF) calculation.

Tests the complete PF pipeline: ACI -> CF/RF/FLF -> PF aggregation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.pf.aggregator import (
    calculate_pf, 
    calculate_pf_batch,
    recalculate_pf_with_weights,
    validate_weights,
    DEFAULT_WEIGHTS
)
from domain.pf import calculate_cf, calculate_rf, calculate_flf
from domain.aci import calculate_aci
from domain.models import DefectInput, PFResult


class TestPFCalculation:
    """Test Priority Factor calculation."""
    
    def test_pf_for_good_condition_asset(self):
        """Good condition (ACI>=80) should have low PF."""
        result = calculate_pf("MANHOLE", 100)
        
        assert result.cf == 0  # No condition-based priority
        assert result.flf == 0  # No life-based priority
        assert result.rf > 0   # Has inherent risk
        
        assert result.pf < 50  # Overall low priority
    
    def test_pf_for_poor_condition_asset(self):
        """Poor condition (ACI<=40) should have high PF."""
        result = calculate_pf("MANHOLE", 20)
        
        assert result.cf > 0   # High condition-based priority
        assert result.flf > 0  # High life-based priority
        
        assert result.pf > result.rf  # Higher than just risk factor
    
    def test_pf_for_critical_asset(self):
        """Critical asset in poor condition should have high PF."""
        result = calculate_pf("TRAFFIC_SIGNAL", 20)
        
        assert result.rf == pytest.approx(100, rel=0.01)  # Highest risk
        assert result.pf > 60  # High priority (CF*0.6 + RF*0.2 + FLF*0.2)
    
    def test_pf_for_low_risk_asset(self):
        """Low-risk asset even in poor condition has moderate PF."""
        result = calculate_pf("BENCHES", 20)
        
        assert result.rf == pytest.approx(10, rel=0.01)  # Lowest risk
        assert result.pf < 80  # Not as high despite poor condition
    
    def test_pf_components_sum_correctly(self):
        """PF should equal weighted sum of components."""
        result = calculate_pf("MANHOLE", 50)
        
        expected_pf = (
            result.weights["cf"] * result.cf +
            result.weights["rf"] * result.rf +
            result.weights["flf"] * result.flf
        )
        
        assert result.pf == pytest.approx(expected_pf, rel=0.01)
    
    def test_pf_uses_default_weights(self):
        """PF should use default weights when none specified."""
        result = calculate_pf("MANHOLE", 50)
        
        assert result.weights["cf"] == DEFAULT_WEIGHTS["cf"]
        assert result.weights["rf"] == DEFAULT_WEIGHTS["rf"]
        assert result.weights["flf"] == DEFAULT_WEIGHTS["flf"]
    
    def test_pf_with_custom_weights(self):
        """PF should respect custom weights."""
        custom_weights = {"cf": 0.7, "rf": 0.2, "flf": 0.1}
        result = calculate_pf("MANHOLE", 50, weights=custom_weights)
        
        assert result.weights == custom_weights


class TestPFBatch:
    """Test batch PF calculation."""
    
    def test_batch_calculation(self):
        """Batch calculation should return results for all items."""
        items = [
            ("MANHOLE", 80),
            ("GULLY", 60),
            ("TRAFFIC_SIGNAL", 40)
        ]
        
        results = calculate_pf_batch(items)
        
        assert len(results) == 3
        assert all(isinstance(r, PFResult) for r in results)
    
    def test_batch_preserves_order(self):
        """Batch results should be in same order as input."""
        items = [
            ("TRAFFIC_SIGNAL", 100),  # Should have low PF
            ("BENCHES", 0),            # Should have high PF
        ]
        
        results = calculate_pf_batch(items)
        
        assert results[0].pf < results[1].pf


class TestWeightRecalculation:
    """Test PF recalculation with different weights."""
    
    def test_recalculate_with_new_weights(self):
        """Recalculating with different weights changes PF."""
        result1 = calculate_pf("MANHOLE", 50)
        
        new_weights = {"cf": 0.8, "rf": 0.1, "flf": 0.1}
        new_pf = recalculate_pf_with_weights(
            result1.cf, result1.rf, result1.flf, new_weights
        )
        
        assert new_pf != result1.pf
    
    def test_recalculate_higher_cf_weight_increases_pf_for_poor_condition(self):
        """Higher CF weight should increase PF for poor condition assets."""
        cf = 75  # Poor condition
        rf = 50  # Medium risk
        flf = 60  # Significant life consumed
        
        normal_pf = recalculate_pf_with_weights(
            cf, rf, flf, {"cf": 0.6, "rf": 0.2, "flf": 0.2}
        )
        high_cf_pf = recalculate_pf_with_weights(
            cf, rf, flf, {"cf": 0.8, "rf": 0.1, "flf": 0.1}
        )
        
        assert high_cf_pf > normal_pf


class TestWeightValidation:
    """Test weight validation."""
    
    def test_valid_weights(self):
        """Weights summing to 1.0 should be valid."""
        assert validate_weights({"cf": 0.6, "rf": 0.2, "flf": 0.2})
        assert validate_weights({"cf": 0.33, "rf": 0.33, "flf": 0.34})
    
    def test_invalid_weights(self):
        """Weights not summing to 1.0 should be invalid."""
        assert not validate_weights({"cf": 0.5, "rf": 0.5, "flf": 0.5})
        assert not validate_weights({"cf": 0.3, "rf": 0.3, "flf": 0.3})


class TestPFIntegration:
    """Integration tests combining ACI and PF."""
    
    def test_full_pipeline_manhole(self):
        """Test complete ACI -> PF pipeline for Manhole."""
        defects = DefectInput(
            functional_defect="No Defect Found",
            appearance_defect="No Defect Found"
        )
        
        aci_result = calculate_aci("MANHOLE", defects)
        pf_result = calculate_pf("MANHOLE", aci_result.aci)
        
        assert aci_result.aci == pytest.approx(100, abs=1)
        assert pf_result.cf == 0
        assert pf_result.flf == 0
    
    def test_full_pipeline_gantry(self):
        """Test complete ACI -> PF pipeline for Gantry."""
        defects = DefectInput(
            foundation_defect="No Defect Found",
            structure_defect="No Defect Found"
        )
        
        aci_result = calculate_aci("GANTRY", defects)
        pf_result = calculate_pf("ROAD_GANTRY", aci_result.aci)
        
        assert aci_result.aci >= 80
        assert pf_result.pf >= 0


class TestPFRanking:
    """Test PF-based asset ranking."""
    
    def test_ranking_poor_before_good(self):
        """Assets in poor condition should rank higher than good."""
        poor_result = calculate_pf("MANHOLE", 30)
        good_result = calculate_pf("MANHOLE", 90)
        
        assert poor_result.pf > good_result.pf
    
    def test_ranking_high_risk_before_low_risk(self):
        """High-risk assets should rank higher at same condition."""
        high_risk = calculate_pf("TRAFFIC_SIGNAL", 60)
        low_risk = calculate_pf("BENCHES", 60)
        
        assert high_risk.pf > low_risk.pf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
