"""
Risk score aggregation and Risk Factor mapping.

The four OAMP risk categories each get a user-entered Probability (1-5) and
Impact (1-5). Per-category score = Probability * Impact (1-25). The total is
the sum across all categories (4-100) and is mapped to RF by direct clamping
into [10, 100].
"""

from typing import Optional, Union

from domain.risk.models import (
    RiskAssessment,
    RiskEntry,
    RiskRegisterSchema,
    PROBABILITY_MIN,
    PROBABILITY_MAX,
    IMPACT_MIN,
    IMPACT_MAX,
)


CATEGORY_COUNT = 4
SCORE_PER_ENTRY_MIN = PROBABILITY_MIN * IMPACT_MIN
SCORE_PER_ENTRY_MAX = PROBABILITY_MAX * IMPACT_MAX
TOTAL_SCORE_MIN = CATEGORY_COUNT * SCORE_PER_ENTRY_MIN
TOTAL_SCORE_MAX = CATEGORY_COUNT * SCORE_PER_ENTRY_MAX

RF_MIN = 10.0
RF_MAX = 100.0


EntryLike = Union[RiskEntry, dict]


def validate_risk_entry(
    probability,
    impact,
    risk_id: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate one (probability, impact) pair against the OAMP 1-5 ranges.

    Returns ``(is_valid, error_message)``. ``error_message`` is empty on
    success and includes the optional ``risk_id`` on failure to help the UI
    point at the offending row.
    """
    prefix = f"Risk {risk_id}: " if risk_id else ""

    try:
        prob_int = int(probability)
    except (TypeError, ValueError):
        return False, f"{prefix}Probability must be an integer (got {probability!r})"

    try:
        impact_int = int(impact)
    except (TypeError, ValueError):
        return False, f"{prefix}Impact must be an integer (got {impact!r})"

    if not (PROBABILITY_MIN <= prob_int <= PROBABILITY_MAX):
        return (
            False,
            f"{prefix}Probability {prob_int} out of range [{PROBABILITY_MIN}-{PROBABILITY_MAX}]",
        )

    if not (IMPACT_MIN <= impact_int <= IMPACT_MAX):
        return (
            False,
            f"{prefix}Impact {impact_int} out of range [{IMPACT_MIN}-{IMPACT_MAX}]",
        )

    return True, ""


def calculate_risk_score(probability, impact) -> int:
    """Per-category score for one risk row.

    Raises ``ValueError`` with a descriptive message if inputs are out of
    range, so UI form handlers can show the validation error verbatim.
    """
    ok, error = validate_risk_entry(probability, impact)
    if not ok:
        raise ValueError(error)
    return int(probability) * int(impact)


def _extract_pi(entry: EntryLike) -> tuple[int, int, Optional[str]]:
    """Pull (probability, impact, risk_id) from a RiskEntry or a dict."""
    if isinstance(entry, RiskEntry):
        return entry.probability, entry.impact, entry.risk_id
    if isinstance(entry, dict):
        return (
            entry.get("probability"),
            entry.get("impact"),
            entry.get("risk_id"),
        )
    raise TypeError(
        f"Risk entry must be RiskEntry or dict, got {type(entry).__name__}"
    )


def aggregate_risk_score(entries: list[EntryLike]) -> int:
    """Sum every entry's Probability * Impact into a single integer.

    Accepts a list of :class:`RiskEntry` or plain dicts so callers (UI, JSON
    loaders, tests) all share the same code path. Raises ``ValueError`` if
    any entry has an invalid score.
    """
    total = 0
    for entry in entries:
        prob, impact, risk_id = _extract_pi(entry)
        ok, error = validate_risk_entry(prob, impact, risk_id)
        if not ok:
            raise ValueError(error)
        total += int(prob) * int(impact)
    return total


def aggregate_from_assessment(assessment: RiskAssessment) -> int:
    """Convenience wrapper that delegates to ``aggregate_risk_score``."""
    return aggregate_risk_score(assessment.entries)


def total_to_rf(total: int) -> float:
    """Map an aggregated total to the Risk Factor by direct clamping.

    Per the OAMP wiring, the aggregated total IS the RF, but clamped into
    [10, 100] so the PF formula stays well-defined. Scores below 10 collapse
    to 10 (very-low-risk floor); scores above 100 collapse to 100 (full
    weight). The float return type matches ``calculate_rf`` for parity with
    the legacy lookup path.
    """
    if total is None:
        raise ValueError("total must be an integer")
    try:
        total_int = int(total)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"total must be coercible to int (got {total!r})") from exc
    clamped = max(int(RF_MIN), min(int(RF_MAX), total_int))
    return float(clamped)


def create_risk_assessment(
    asset_id: str,
    asset_type: str,
    risk_inputs: dict,
    schema: Optional[RiskRegisterSchema] = None,
    notes: Optional[str] = None,
) -> RiskAssessment:
    """Build a :class:`RiskAssessment` from a flat input dict.

    ``risk_inputs`` keys are risk IDs. Values may be:

    - a 2-tuple ``(probability, impact)``
    - a 3-tuple ``(probability, impact, description)``
    - a dict ``{"probability": int, "impact": int, "description": str}``

    The schema is used to denormalize the category name onto each entry so
    downstream consumers can render the assessment without re-loading the
    schema. The schema is optional - if not supplied the entry's ``category``
    is left blank.
    """
    entries: list[RiskEntry] = []
    for risk_id, value in risk_inputs.items():
        if isinstance(value, dict):
            prob = value.get("probability")
            impact = value.get("impact")
            description = value.get("description", "")
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                prob, impact = value
                description = ""
            elif len(value) == 3:
                prob, impact, description = value
            else:
                raise ValueError(
                    f"Risk {risk_id}: expected 2 or 3 values, got {len(value)}"
                )
        else:
            raise TypeError(
                f"Risk {risk_id}: input must be tuple or dict (got {type(value).__name__})"
            )

        category_name = ""
        if schema is not None:
            cat = schema.get_category(risk_id)
            if cat is not None:
                category_name = cat.name

        entries.append(
            RiskEntry(
                risk_id=risk_id,
                category=category_name,
                probability=prob,
                impact=impact,
                description=description or "",
            )
        )

    return RiskAssessment(
        asset_id=asset_id,
        asset_type=asset_type,
        entries=entries,
        notes=notes,
    )
