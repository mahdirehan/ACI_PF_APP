"""
Data models for per-asset OAMP risk assessment.

A risk assessment captures the user-defined Probability x Impact scores for
each of the four high-level OAMP risk categories (R001-R004). The summed
total directly becomes the Risk Factor (clamped to 10-100).
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


PROBABILITY_MIN = 1
PROBABILITY_MAX = 5
IMPACT_MIN = 1
IMPACT_MAX = 5


class RiskCategory(BaseModel):
    """Schema definition for a single OAMP risk category."""

    risk_id: str = Field(description="Risk identifier (e.g., 'R001')")
    name: str = Field(description="Category name (e.g., 'A. Natural Events and Hazards')")
    description: str = Field(default="", description="Optional schema-level description")


class RiskRegisterSchema(BaseModel):
    """Top-level schema describing the fixed OAMP risk categories."""

    version: str = Field(default="OAMP-2025", description="Schema version tag")
    categories: list[RiskCategory] = Field(
        default_factory=list,
        description="Ordered list of risk categories the user fills in per asset",
    )

    @property
    def risk_ids(self) -> list[str]:
        """All risk IDs declared in the schema."""
        return [cat.risk_id for cat in self.categories]

    @property
    def category_count(self) -> int:
        """Number of categories in the schema."""
        return len(self.categories)

    def get_category(self, risk_id: str) -> Optional[RiskCategory]:
        """Look up a category by its risk ID."""
        for cat in self.categories:
            if cat.risk_id == risk_id:
                return cat
        return None


class RiskEntry(BaseModel):
    """A single user-entered risk row for one category of one asset."""

    risk_id: str = Field(description="Risk identifier matching the schema")
    category: str = Field(default="", description="Category name (denormalized for display)")
    probability: int = Field(
        ge=PROBABILITY_MIN,
        le=PROBABILITY_MAX,
        description="Probability / Likelihood (1-5)",
    )
    impact: int = Field(
        ge=IMPACT_MIN,
        le=IMPACT_MAX,
        description="Impact / Severity (1-5)",
    )
    description: str = Field(
        default="",
        description="Free-text description of the specific risk for this asset",
    )

    @field_validator("probability", "impact", mode="before")
    @classmethod
    def _coerce_int(cls, value):
        """Coerce string/float inputs to int (UIs often send strings)."""
        if value is None:
            return value
        if isinstance(value, bool):
            raise TypeError("Boolean is not a valid score")
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("Empty string is not a valid score")
            return int(float(stripped))
        return value

    @property
    def score(self) -> int:
        """Risk score for this row = probability * impact (1-25)."""
        return self.probability * self.impact


class RiskAssessment(BaseModel):
    """Complete per-asset risk assessment across all categories."""

    model_config = ConfigDict(extra="allow")

    asset_id: str = Field(description="Asset identifier")
    asset_type: str = Field(default="", description="Asset type (for reference / auditing)")
    entries: list[RiskEntry] = Field(
        default_factory=list,
        description="One RiskEntry per category in the schema",
    )
    notes: Optional[str] = Field(default=None, description="Free-text assessor notes")

    @property
    def total_score(self) -> int:
        """Aggregated total = sum of every entry's probability * impact."""
        return sum(entry.score for entry in self.entries)

    @property
    def entry_count(self) -> int:
        """Number of categories that were assessed."""
        return len(self.entries)

    def get_entry(self, risk_id: str) -> Optional[RiskEntry]:
        """Find an entry by its risk ID, or None if missing."""
        for entry in self.entries:
            if entry.risk_id == risk_id:
                return entry
        return None
