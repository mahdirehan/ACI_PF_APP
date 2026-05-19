"""
Unit tests for Condition Factor (CF) calculation.

Tests the Excel formula: =IF(ACI>=80, 0, (80-ACI)/80*100)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.pf.cf import calculate_cf, CF_THRESHOLD, CF_MAX, CF_MIN


class TestConditionFactor:
    """Test CF calculation against Excel formula."""
    
    def test_cf_at_perfect_condition(self):
        """ACI=100 should give CF=0 (no priority boost)."""
        assert calculate_cf(100) == 0.0
    
    def test_cf_at_good_threshold(self):
        """ACI=80 (GOOD threshold) should give CF=0."""
        assert calculate_cf(80) == 0.0
    
    def test_cf_at_just_below_threshold(self):
        """ACI=79 should give small positive CF."""
        cf = calculate_cf(79)
        assert cf > 0
        assert cf == pytest.approx(1.25, rel=0.01)
    
    def test_cf_at_fair_midpoint(self):
        """ACI=40 (midpoint of FAIR range) should give CF=50."""
        assert calculate_cf(40) == pytest.approx(50.0, rel=0.01)
    
    def test_cf_at_poor_threshold(self):
        """ACI=40 (POOR threshold) should give CF=50."""
        assert calculate_cf(40) == pytest.approx(50.0, rel=0.01)
    
    def test_cf_at_worst_condition(self):
        """ACI=0 (worst) should give CF=100 (maximum priority)."""
        assert calculate_cf(0) == 100.0
    
    def test_cf_linear_scaling(self):
        """CF should scale linearly between ACI 0-80."""
        cf_20 = calculate_cf(20)
        cf_40 = calculate_cf(40)
        cf_60 = calculate_cf(60)
        
        assert cf_20 == pytest.approx(75.0, rel=0.01)
        assert cf_60 == pytest.approx(25.0, rel=0.01)
        assert cf_40 - cf_60 == pytest.approx(cf_20 - cf_40, rel=0.01)
    
    def test_cf_above_threshold_all_zero(self):
        """All ACI values >= 80 should give CF=0."""
        for aci in [80, 85, 90, 95, 100]:
            assert calculate_cf(aci) == 0.0
    
    @pytest.mark.parametrize("aci,expected_cf", [
        (0, 100.0),
        (10, 87.5),
        (20, 75.0),
        (30, 62.5),
        (40, 50.0),
        (50, 37.5),
        (60, 25.0),
        (70, 12.5),
        (79, 1.25),
        (80, 0.0),
        (100, 0.0),
    ])
    def test_cf_lookup_table_values(self, aci, expected_cf):
        """Test CF values that would appear in the 101-row lookup table."""
        assert calculate_cf(aci) == pytest.approx(expected_cf, rel=0.01)
    
    def test_cf_constants(self):
        """Verify module constants."""
        assert CF_THRESHOLD == 80
        assert CF_MAX == 100.0
        assert CF_MIN == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
