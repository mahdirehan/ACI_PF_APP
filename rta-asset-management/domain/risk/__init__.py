"""
Per-asset OAMP risk scoring.

The user enters Probability (1-5) and Impact (1-5) for each of four
high-level risk categories (R001-R004). Per-category score is
Probability * Impact (1-25). The total across all four categories (4-100)
maps to the Risk Factor by direct clamping into [10, 100].

Modules:
- models:      Pydantic data shapes (RiskEntry, RiskAssessment, schema)
- aggregator:  Pure scoring/validation/RF mapping functions
- loader:      Schema + assessments JSON I/O (cached)
"""

from domain.risk.models import (
    RiskEntry,
    RiskAssessment,
    RiskCategory,
    RiskRegisterSchema,
    PROBABILITY_MIN,
    PROBABILITY_MAX,
    IMPACT_MIN,
    IMPACT_MAX,
)
from domain.risk.aggregator import (
    validate_risk_entry,
    calculate_risk_score,
    aggregate_risk_score,
    aggregate_from_assessment,
    total_to_rf,
    create_risk_assessment,
    CATEGORY_COUNT,
    SCORE_PER_ENTRY_MIN,
    SCORE_PER_ENTRY_MAX,
    TOTAL_SCORE_MIN,
    TOTAL_SCORE_MAX,
    RF_MIN,
    RF_MAX,
)
from domain.risk.loader import (
    load_risk_register_schema,
    get_risk_categories,
    get_risk_category_by_id,
    load_risk_assessments_file,
    save_risk_assessments_file,
    clear_cache,
)

__all__ = [
    # Models
    "RiskEntry",
    "RiskAssessment",
    "RiskCategory",
    "RiskRegisterSchema",
    # Aggregation
    "validate_risk_entry",
    "calculate_risk_score",
    "aggregate_risk_score",
    "aggregate_from_assessment",
    "total_to_rf",
    "create_risk_assessment",
    # Loader
    "load_risk_register_schema",
    "get_risk_categories",
    "get_risk_category_by_id",
    "load_risk_assessments_file",
    "save_risk_assessments_file",
    "clear_cache",
    # Constants
    "PROBABILITY_MIN",
    "PROBABILITY_MAX",
    "IMPACT_MIN",
    "IMPACT_MAX",
    "CATEGORY_COUNT",
    "SCORE_PER_ENTRY_MIN",
    "SCORE_PER_ENTRY_MAX",
    "TOTAL_SCORE_MIN",
    "TOTAL_SCORE_MAX",
    "RF_MIN",
    "RF_MAX",
]
