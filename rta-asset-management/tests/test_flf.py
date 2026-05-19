"""
Unit tests for Functional Life Factor (FLF) calculation.

Tests the Excel formula:
=IF(ACI=0, 100, IF(ACI>=80, 0, MAX(0, MIN(100, (ConsumedLife/TotalLife)*100))))
Where ConsumedLife = (ACI - intercept) / slope
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.pf.flf import (
    calculate_flf, 
    calculate_flf_with_curve,
    get_consumed_life,
    get_remaining_life,
    get_deterioration_curve,
    list_asset_types_with_flf,
    FLF_MIN, 
    FLF_MAX
)


class TestFunctionalLifeFactor:
    """Test FLF calculation against Excel formula."""
    
    def test_flf_at_perfect_condition(self):
        """ACI=100 (perfect) should give FLF=0."""
        flf = calculate_flf("MANHOLE", 100)
        assert flf == 0.0
    
    def test_flf_at_good_threshold(self):
        """ACI=80 (GOOD threshold) should give FLF=0."""
        flf = calculate_flf("MANHOLE", 80)
        assert flf == 0.0
    
    def test_flf_at_failed_condition(self):
        """ACI=0 (failed) should give FLF=100."""
        flf = calculate_flf("MANHOLE", 0)
        assert flf == 100.0
    
    def test_flf_mid_range(self):
        """ACI in 40-79 range should give FLF between 0 and 100."""
        flf = calculate_flf("MANHOLE", 50)
        assert 0 < flf < 100
    
    def test_flf_clamped_to_bounds(self):
        """FLF should always be between 0 and 100."""
        for aci in range(0, 101, 10):
            flf = calculate_flf("MANHOLE", aci)
            assert FLF_MIN <= flf <= FLF_MAX
    
    def test_flf_unknown_asset_returns_zero(self):
        """Assets without FLF curve should return 0."""
        flf = calculate_flf("UNKNOWN_ASSET", 50)
        assert flf == 0.0
    
    def test_flf_with_explicit_curve(self):
        """Test FLF calculation with explicit curve parameters."""
        flf = calculate_flf_with_curve(
            aci=50,
            intercept=102.22,
            slope=-3.2661,
            total_life=31.0
        )
        assert 0 < flf < 100
    
    def test_consumed_life_calculation(self):
        """Test consumed life years calculation."""
        consumed = get_consumed_life("MANHOLE", 80)
        assert consumed is not None
        assert consumed >= 0
    
    def test_remaining_life_calculation(self):
        """Test remaining life years calculation."""
        remaining = get_remaining_life("MANHOLE", 80)
        assert remaining is not None
        assert remaining >= 0
    
    def test_deterioration_curve_exists(self):
        """Test that deterioration curves can be retrieved."""
        curve = get_deterioration_curve("MANHOLE")
        assert curve is not None
        assert curve.intercept > 0
        assert curve.slope < 0  # Negative for deterioration
        assert curve.total_life > 0
    
    def test_list_asset_types_with_flf(self):
        """Test that asset types with FLF are listed."""
        assets = list_asset_types_with_flf()
        assert len(assets) >= 20  # Should have ~29 assets with FLF
        assert "MANHOLE" in assets
    
    @pytest.mark.parametrize("asset_type", [
        "MANHOLE", "GULLY", "ROAD_SIGN", "CRASH_CUSHION",
        "GUARD_RAIL", "BARRIER", "FENCE", "FOOTPATH"
    ])
    def test_flf_decreases_with_better_condition(self, asset_type):
        """FLF should decrease as ACI improves (for same asset type)."""
        flf_40 = calculate_flf(asset_type, 40)
        flf_60 = calculate_flf(asset_type, 60)
        flf_79 = calculate_flf(asset_type, 79)
        
        assert flf_40 >= flf_60 >= flf_79 >= 0
    
    @pytest.mark.parametrize("asset_type,expected_total_life", [
        ("MANHOLE", 31.0),
        ("ROAD_SIGN", 13.0),
        ("GULLY", 38.7),
        ("FOOTPATH", 38.0),
    ])
    def test_known_total_life_values(self, asset_type, expected_total_life):
        """Test that total life values match Excel data."""
        curve = get_deterioration_curve(asset_type)
        assert curve is not None
        assert curve.total_life == pytest.approx(expected_total_life, rel=0.01)
    
    def test_flf_edge_case_at_threshold(self):
        """Test FLF at exactly ACI=80 (edge case)."""
        for asset in list_asset_types_with_flf()[:5]:
            flf = calculate_flf(asset, 80)
            assert flf == 0.0
    
    def test_flf_constants(self):
        """Verify module constants."""
        assert FLF_MIN == 0.0
        assert FLF_MAX == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
