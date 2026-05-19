"""
Unit tests for the per-asset OAMP risk scoring module.

Covers:
- RiskEntry score math (Probability x Impact)
- Validation of out-of-range inputs
- aggregate_risk_score on dict and RiskEntry inputs
- total_to_rf direct-clamp mapping into [10, 100]
- create_risk_assessment end-to-end with the four OAMP categories
- Schema loader returns four expected categories
- load_risk_assessments_file round-trip
- Integration: calculate_rf / calculate_pf with override_score
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.risk import (
    CATEGORY_COUNT,
    PROBABILITY_MAX,
    PROBABILITY_MIN,
    IMPACT_MAX,
    IMPACT_MIN,
    RF_MAX,
    RF_MIN,
    RiskAssessment,
    RiskEntry,
    TOTAL_SCORE_MAX,
    TOTAL_SCORE_MIN,
    aggregate_from_assessment,
    aggregate_risk_score,
    calculate_risk_score,
    create_risk_assessment,
    get_risk_categories,
    load_risk_assessments_file,
    load_risk_register_schema,
    save_risk_assessments_file,
    total_to_rf,
    validate_risk_entry,
)
from domain.pf.rf import (
    calculate_rf,
    calculate_rf_from_assessment,
    _RF_CACHE,
)
from domain.pf.aggregator import calculate_pf


def _clear_rf_cache():
    """Drop cached RF values so legacy/override paths can be tested in isolation."""
    _RF_CACHE.clear()


class TestRiskEntryScore:
    """Per-category Probability x Impact math."""

    def test_min_score(self):
        entry = RiskEntry(risk_id="R001", probability=1, impact=1)
        assert entry.score == 1

    def test_max_score(self):
        entry = RiskEntry(risk_id="R001", probability=5, impact=5)
        assert entry.score == 25

    @pytest.mark.parametrize(
        "probability,impact,expected",
        [(3, 4, 12), (2, 5, 10), (4, 3, 12), (1, 5, 5), (5, 1, 5)],
    )
    def test_mid_values(self, probability, impact, expected):
        entry = RiskEntry(risk_id="R001", probability=probability, impact=impact)
        assert entry.score == expected

    def test_coerces_string_input(self):
        """UIs often send form values as strings - they must coerce cleanly."""
        entry = RiskEntry(risk_id="R001", probability="3", impact="4")
        assert entry.probability == 3
        assert entry.impact == 4
        assert entry.score == 12


class TestRiskEntryValidation:
    """Out-of-range scores must be rejected at the model layer."""

    def test_probability_below_min_rejected(self):
        with pytest.raises(Exception):
            RiskEntry(risk_id="R001", probability=0, impact=3)

    def test_probability_above_max_rejected(self):
        with pytest.raises(Exception):
            RiskEntry(risk_id="R001", probability=6, impact=3)

    def test_impact_below_min_rejected(self):
        with pytest.raises(Exception):
            RiskEntry(risk_id="R001", probability=3, impact=0)

    def test_impact_above_max_rejected(self):
        with pytest.raises(Exception):
            RiskEntry(risk_id="R001", probability=3, impact=6)


class TestValidateRiskEntry:
    """Standalone validator returns (ok, message) without raising."""

    def test_valid_pair(self):
        ok, error = validate_risk_entry(3, 4)
        assert ok is True
        assert error == ""

    def test_invalid_probability_message(self):
        ok, error = validate_risk_entry(6, 3, risk_id="R001")
        assert ok is False
        assert "R001" in error
        assert "Probability" in error

    def test_invalid_impact_message(self):
        ok, error = validate_risk_entry(3, 9, risk_id="R002")
        assert ok is False
        assert "Impact" in error

    def test_non_numeric_input(self):
        ok, error = validate_risk_entry("abc", 3)
        assert ok is False


class TestAggregator:
    """Score summation across all categories."""

    def test_aggregate_dicts(self):
        entries = [
            {"risk_id": "R001", "probability": 3, "impact": 3},  # 9
            {"risk_id": "R002", "probability": 2, "impact": 4},  # 8
            {"risk_id": "R003", "probability": 5, "impact": 2},  # 10
            {"risk_id": "R004", "probability": 1, "impact": 1},  # 1
        ]
        assert aggregate_risk_score(entries) == 28

    def test_aggregate_entries(self):
        entries = [
            RiskEntry(risk_id="R001", probability=3, impact=3),
            RiskEntry(risk_id="R002", probability=2, impact=4),
            RiskEntry(risk_id="R003", probability=5, impact=2),
            RiskEntry(risk_id="R004", probability=1, impact=1),
        ]
        assert aggregate_risk_score(entries) == 28

    def test_aggregate_mixed_inputs_match(self):
        dict_total = aggregate_risk_score(
            [{"risk_id": "R001", "probability": 4, "impact": 5}]
        )
        entry_total = aggregate_risk_score(
            [RiskEntry(risk_id="R001", probability=4, impact=5)]
        )
        assert dict_total == entry_total == 20

    def test_aggregate_rejects_bad_dict(self):
        with pytest.raises(ValueError):
            aggregate_risk_score([{"risk_id": "R001", "probability": 6, "impact": 3}])

    def test_calculate_risk_score(self):
        assert calculate_risk_score(3, 4) == 12
        assert calculate_risk_score(5, 5) == 25
        assert calculate_risk_score(1, 1) == 1

    def test_calculate_risk_score_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            calculate_risk_score(0, 3)


class TestTotalToRf:
    """Direct-clamp mapping aggregated total -> RF in [10, 100]."""

    @pytest.mark.parametrize(
        "total,expected",
        [
            (4, 10.0),        # below floor -> clamp
            (9, 10.0),        # still below floor
            (10, 10.0),       # at floor
            (50, 50.0),       # mid range pass-through
            (87, 87.0),       # sample from OAMP screenshot
            (100, 100.0),     # at ceiling
            (150, 100.0),     # above ceiling -> clamp
        ],
    )
    def test_clamp(self, total, expected):
        assert total_to_rf(total) == pytest.approx(expected)

    def test_returns_float(self):
        assert isinstance(total_to_rf(50), float)

    def test_below_zero_clamped(self):
        assert total_to_rf(-100) == 10.0

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            total_to_rf("not a number")


class TestCreateAssessment:
    """End-to-end UI convenience builder with the four OAMP categories."""

    def test_tuple_inputs(self):
        schema = load_risk_register_schema()
        inputs = {
            "R001": (3, 3),
            "R002": (2, 4),
            "R003": (5, 5),
            "R004": (1, 2),
        }
        assessment = create_risk_assessment(
            asset_id="ASSET_001",
            asset_type="CRASH_CUSHION",
            risk_inputs=inputs,
            schema=schema,
        )
        assert assessment.asset_id == "ASSET_001"
        assert assessment.asset_type == "CRASH_CUSHION"
        assert assessment.entry_count == 4
        assert assessment.total_score == 9 + 8 + 25 + 2  # 44
        assert assessment.get_entry("R003").score == 25

    def test_tuple_with_description(self):
        inputs = {
            "R001": (3, 3, "Sandstorms"),
            "R002": (2, 4, ""),
            "R003": (4, 5, "Visible corrosion"),
            "R004": (1, 1, ""),
        }
        assessment = create_risk_assessment("ASSET_002", "MANHOLE", inputs)
        r001 = assessment.get_entry("R001")
        assert r001.description == "Sandstorms"
        assert assessment.total_score == 9 + 8 + 20 + 1

    def test_dict_inputs(self):
        inputs = {
            "R001": {"probability": 3, "impact": 3, "description": "x"},
            "R002": {"probability": 2, "impact": 2, "description": ""},
            "R003": {"probability": 1, "impact": 5},
            "R004": {"probability": 5, "impact": 1},
        }
        assessment = create_risk_assessment("ASSET_003", "BENCHES", inputs)
        assert assessment.total_score == 9 + 4 + 5 + 5

    def test_min_and_max_totals(self):
        schema = load_risk_register_schema()
        floor_inputs = {rid: (1, 1) for rid in schema.risk_ids}
        ceiling_inputs = {rid: (5, 5) for rid in schema.risk_ids}
        floor = create_risk_assessment("X", "Y", floor_inputs, schema=schema)
        ceiling = create_risk_assessment("X", "Y", ceiling_inputs, schema=schema)
        assert floor.total_score == TOTAL_SCORE_MIN
        assert ceiling.total_score == TOTAL_SCORE_MAX

    def test_aggregate_from_assessment(self):
        inputs = {"R001": (3, 3), "R002": (2, 4), "R003": (4, 5), "R004": (2, 2)}
        assessment = create_risk_assessment("A", "B", inputs)
        assert aggregate_from_assessment(assessment) == assessment.total_score


class TestSchemaLoader:
    """The shipped schema JSON has the four expected OAMP categories."""

    def test_loads_four_categories(self):
        schema = load_risk_register_schema()
        assert schema.category_count == CATEGORY_COUNT

    def test_expected_risk_ids(self):
        schema = load_risk_register_schema()
        assert schema.risk_ids == ["R001", "R002", "R003", "R004"]

    def test_get_risk_categories(self):
        cats = get_risk_categories()
        assert len(cats) == CATEGORY_COUNT
        names = [c.name for c in cats]
        assert "A. Natural Events and Hazards" in names
        assert "B. External Impacts on The Agency" in names
        assert "C. Physical Asset Failures" in names
        assert "D. Operational Risk Events" in names

    def test_missing_category_returns_none(self):
        schema = load_risk_register_schema()
        assert schema.get_category("R999") is None


class TestAssessmentsFileRoundTrip:
    """The UI's JSON contract: save -> load -> equal."""

    def test_round_trip(self, tmp_path):
        path = tmp_path / "assessments.json"
        inputs = {
            "R001": (3, 3, "Sandstorms"),
            "R002": (2, 4, ""),
            "R003": (4, 5, "Corrosion"),
            "R004": (2, 2, ""),
        }
        assessment = create_risk_assessment("ASSET_001", "CRASH_CUSHION", inputs)
        saved = {assessment.asset_id: assessment}

        save_risk_assessments_file(path, saved)
        loaded = load_risk_assessments_file(path)

        assert set(loaded.keys()) == {"ASSET_001"}
        out = loaded["ASSET_001"]
        assert out.asset_type == "CRASH_CUSHION"
        assert out.entry_count == 4
        assert out.total_score == assessment.total_score
        assert out.get_entry("R001").description == "Sandstorms"

    def test_missing_file_returns_empty(self, tmp_path):
        path = tmp_path / "does-not-exist.json"
        assert load_risk_assessments_file(path) == {}

    def test_payload_shape(self, tmp_path):
        """Verify the on-disk JSON matches the documented contract."""
        path = tmp_path / "assessments.json"
        inputs = {"R001": (3, 3), "R002": (2, 4), "R003": (1, 1), "R004": (5, 5)}
        assessment = create_risk_assessment("A1", "MANHOLE", inputs)
        save_risk_assessments_file(path, {"A1": assessment})

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "assessments" in data
        assert len(data["assessments"]) == 1
        item = data["assessments"][0]
        assert item["asset_id"] == "A1"
        assert len(item["entries"]) == 4


class TestRfOverrideIntegration:
    """calculate_rf must honor override_score without breaking legacy callers."""

    def setup_method(self):
        _clear_rf_cache()

    def teardown_method(self):
        _clear_rf_cache()

    def test_legacy_path_unchanged_traffic_signal(self):
        rf = calculate_rf("TRAFFIC_SIGNAL")
        assert rf == pytest.approx(100.0, rel=0.01)

    def test_legacy_path_unchanged_benches(self):
        rf = calculate_rf("BENCHES")
        assert rf == pytest.approx(10.0, rel=0.01)

    @pytest.mark.parametrize(
        "override,expected_rf",
        [(4, 10.0), (50, 50.0), (87, 87.0), (100, 100.0), (200, 100.0)],
    )
    def test_override_skips_legacy_pool(self, override, expected_rf):
        rf = calculate_rf("BENCHES", override_score=override)
        assert rf == pytest.approx(expected_rf)

    def test_override_does_not_pollute_legacy_cache(self):
        legacy_rf = calculate_rf("MANHOLE")
        _ = calculate_rf("MANHOLE", override_score=90)
        legacy_rf_again = calculate_rf("MANHOLE")
        assert legacy_rf == legacy_rf_again

    def test_calculate_rf_from_assessment(self):
        inputs = {"R001": (3, 3), "R002": (2, 4), "R003": (4, 5), "R004": (2, 2)}
        assessment = create_risk_assessment("ASSET_001", "CRASH_CUSHION", inputs)
        rf = calculate_rf_from_assessment(assessment)
        assert rf == pytest.approx(float(assessment.total_score))


class TestPfWithOverride:
    """calculate_pf forwards the override into RF."""

    def setup_method(self):
        _clear_rf_cache()

    def teardown_method(self):
        _clear_rf_cache()

    def test_pf_uses_override(self):
        result_legacy = calculate_pf("MANHOLE", aci=60)
        result_override = calculate_pf("MANHOLE", aci=60, risk_score_override=87)
        assert result_override.rf == pytest.approx(87.0)
        assert result_override.cf == pytest.approx(result_legacy.cf)
        assert result_override.flf == pytest.approx(result_legacy.flf)

    def test_pf_override_changes_total(self):
        a = calculate_pf("MANHOLE", aci=60)
        b = calculate_pf("MANHOLE", aci=60, risk_score_override=100)
        assert b.pf != a.pf


class TestRfBounds:
    """Constants exposed by the risk module match the RF formula contract."""

    def test_constants(self):
        assert PROBABILITY_MIN == 1
        assert PROBABILITY_MAX == 5
        assert IMPACT_MIN == 1
        assert IMPACT_MAX == 5
        assert CATEGORY_COUNT == 4
        assert TOTAL_SCORE_MIN == 4
        assert TOTAL_SCORE_MAX == 100
        assert RF_MIN == 10.0
        assert RF_MAX == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
