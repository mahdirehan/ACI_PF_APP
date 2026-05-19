"""
Unit tests for Risk Factor (RF) calculation.

Tests the Excel formula: =10+((Score-MIN)/(MAX-MIN))*(100-10)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.pf.rf import calculate_rf, get_all_rf_values, get_priority_level, RF_MIN, RF_MAX


class TestRiskFactor:
    """Test RF calculation against Excel formula."""
    
    def test_rf_highest_risk_asset(self):
        """Traffic Signal (risk score 117) should give RF=100."""
        rf = calculate_rf("TRAFFIC_SIGNAL")
        assert rf == pytest.approx(100.0, rel=0.01)
    
    def test_rf_lowest_risk_asset(self):
        """Benches (risk score 60) should give RF=10."""
        rf = calculate_rf("BENCHES")
        assert rf == pytest.approx(10.0, rel=0.01)
    
    def test_rf_mid_range_asset(self):
        """Manhole (risk score 79) should give mid-range RF."""
        rf = calculate_rf("MANHOLE")
        assert RF_MIN < rf < RF_MAX
    
    def test_rf_within_bounds(self):
        """All RF values should be between 10 and 100."""
        all_rf = get_all_rf_values()
        for asset_type, rf in all_rf.items():
            assert RF_MIN <= rf <= RF_MAX, f"{asset_type} RF out of bounds: {rf}"
    
    def test_rf_high_priority_assets(self):
        """High priority assets should have higher RF."""
        traffic_signal_rf = calculate_rf("TRAFFIC_SIGNAL")
        road_sign_rf = calculate_rf("ROAD_SIGN")
        benches_rf = calculate_rf("BENCHES")
        
        assert traffic_signal_rf > road_sign_rf > benches_rf
    
    def test_rf_unknown_asset_raises(self):
        """Unknown asset type should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_rf("UNKNOWN_ASSET_TYPE")
    
    def test_rf_normalized_range(self):
        """RF should span from 10 to 100 across all assets."""
        all_rf = get_all_rf_values()
        rf_values = list(all_rf.values())
        
        assert min(rf_values) == pytest.approx(10.0, rel=0.01)
        assert max(rf_values) == pytest.approx(100.0, rel=0.01)
    
    @pytest.mark.parametrize("asset_type,expected_priority", [
        ("TRAFFIC_SIGNAL", "H"),
        ("ROAD_SIGN", "H"),
        ("MANHOLE", "M"),
        ("GULLY", "M"),
        ("BENCHES", "L"),
        ("LANDSCAPE", "L"),
    ])
    def test_priority_levels(self, asset_type, expected_priority):
        """Test priority level classification."""
        assert get_priority_level(asset_type) == expected_priority
    
    @pytest.mark.parametrize("asset_type", [
        "TRAFFIC_SIGNAL", "ROAD_SIGN", "STREETLIGHT", "CRASH_CUSHION",
        "ROAD_MARKING", "ROAD_HUMP", "ROAD_STUDS", "BARRIER",
    ])
    def test_high_priority_assets_have_high_rf(self, asset_type):
        """High priority assets should have RF >= 50."""
        rf = calculate_rf(asset_type)
        assert rf >= 50, f"{asset_type} should have RF >= 50, got {rf}"
    
    @pytest.mark.parametrize("asset_type", [
        "GUARDRAIL", "ROAD_GANTRY", "PEDESTRIAN_CROSSING", "FENCE",
    ])
    def test_mid_high_priority_assets_have_moderate_rf(self, asset_type):
        """Mid-high priority assets should have RF >= 40."""
        rf = calculate_rf(asset_type)
        assert rf >= 40, f"{asset_type} should have RF >= 40, got {rf}"
    
    def test_rf_constants(self):
        """Verify module constants."""
        assert RF_MIN == 10.0
        assert RF_MAX == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
