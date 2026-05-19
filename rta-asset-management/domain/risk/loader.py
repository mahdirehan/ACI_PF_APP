"""
Loaders for the OAMP risk register schema and per-asset assessment files.

Mirrors the pattern in ``domain/lookups/loader.py``: cached JSON read for the
schema, and a small helper that converts a UI-produced assessments JSON file
into a dict keyed by ``asset_id`` for the master priority pipeline.
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional, Union

from domain.risk.models import RiskAssessment, RiskCategory, RiskEntry, RiskRegisterSchema


LOOKUPS_DIR = Path(__file__).resolve().parent.parent / "lookups"
RISK_SCHEMA_FILE = LOOKUPS_DIR / "risk_register_schema.json"


_DEFAULT_CATEGORIES: list[dict] = [
    {"risk_id": "R001", "name": "A. Natural Events and Hazards"},
    {"risk_id": "R002", "name": "B. External Impacts on The Agency"},
    {"risk_id": "R003", "name": "C. Physical Asset Failures"},
    {"risk_id": "R004", "name": "D. Operational Risk Events"},
]


def _build_default_schema() -> RiskRegisterSchema:
    """Embedded fallback schema used if the JSON file is missing."""
    categories = [RiskCategory(**c) for c in _DEFAULT_CATEGORIES]
    return RiskRegisterSchema(version="OAMP-2025", categories=categories)


@lru_cache(maxsize=1)
def load_risk_register_schema() -> RiskRegisterSchema:
    """Load the OAMP risk register schema from JSON, cached for the process.

    Falls back to the embedded default if the file is missing. The cache lets
    callers (UI, calculators, tests) treat this as a cheap constant.
    """
    if not RISK_SCHEMA_FILE.exists():
        return _build_default_schema()

    with open(RISK_SCHEMA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = [RiskCategory(**cat) for cat in data.get("categories", [])]
    return RiskRegisterSchema(
        version=data.get("version", "OAMP-2025"),
        categories=categories,
    )


def get_risk_categories() -> list[RiskCategory]:
    """Return the schema's categories in declared order."""
    return load_risk_register_schema().categories


def get_risk_category_by_id(risk_id: str) -> Optional[RiskCategory]:
    """Look up a single category by its risk ID, or ``None`` if absent."""
    return load_risk_register_schema().get_category(risk_id)


def clear_cache() -> None:
    """Drop the cached schema. Useful for tests and live edits."""
    load_risk_register_schema.cache_clear()


def load_risk_assessments_file(
    path: Union[str, Path],
) -> dict[str, RiskAssessment]:
    """Read a UI-produced assessments JSON file into a dict by ``asset_id``.

    Expected payload shape::

        {
            "version": "OAMP-2025",
            "assessments": [
                {
                    "asset_id": "ASSET_001",
                    "asset_type": "CRASH_CUSHION",
                    "entries": [
                        {"risk_id": "R001", "probability": 3, "impact": 3,
                         "description": "..."}
                    ],
                    "notes": "..."
                }
            ]
        }

    Duplicate ``asset_id`` entries keep the last one (UIs may emit corrections
    by appending). Returns an empty dict when the file is missing.
    """
    file_path = Path(path)
    if not file_path.exists():
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assessments_raw = data.get("assessments", [])
    out: dict[str, RiskAssessment] = {}
    for item in assessments_raw:
        entries = [RiskEntry(**entry) for entry in item.get("entries", [])]
        assessment = RiskAssessment(
            asset_id=str(item.get("asset_id", "")),
            asset_type=str(item.get("asset_type", "")),
            entries=entries,
            notes=item.get("notes"),
        )
        if not assessment.asset_id:
            continue
        out[assessment.asset_id] = assessment

    return out


def save_risk_assessments_file(
    path: Union[str, Path],
    assessments: dict[str, RiskAssessment],
    version: str = "OAMP-2025",
) -> Path:
    """Serialize a dict of assessments back to the canonical JSON shape.

    Provided for symmetry with :func:`load_risk_assessments_file` and to give
    the UI a single source of truth for the on-disk format.
    """
    file_path = Path(path)
    payload = {
        "version": version,
        "assessments": [
            assessment.model_dump(mode="json")
            for assessment in assessments.values()
        ],
    }
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return file_path
