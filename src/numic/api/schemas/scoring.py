"""API request/response models for scoring endpoints (Pydantic)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from numic.core.config import DEFAULT_SCORE_VERSION

_SCORE_VERSION_DESCRIPTION = "Rule set, e.g. numic_flow_levene or a pinned revision numic_flow_levene@1."


def _age_field():
    return Field(
        None,
        ge=20,
        le=60,
        description=(
            "Age at scan in weeks (gestational age at birth + day of life / 7). "
            "Required by rule sets with age-based lines such as numic_flow_levene."
        ),
    )


class RiskTier(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class VentricularMeasurements(BaseModel):
    """Single-timepoint VI / AHW / TOD from cUS overlay or manual entry."""

    vi_mm: float = Field(
        ...,
        description="Ventricular index (mm). When left and right are measured, score the larger side.",
    )
    ahw_mm: float = Field(..., description="Anterior horn width (mm).")
    tod_mm: float = Field(..., description="Thalamo-occipital distance (mm).")


class MetricScore(BaseModel):
    """How one static metric was scored, so the result can be explained."""

    value_mm: float
    points: int = Field(..., ge=0, le=2)
    kind: Literal["fixed", "reference_line"]
    one_point_mm: float = Field(..., description="1 point at or above this mm.")
    two_point_mm: float = Field(..., description="2 points from this mm (see two_point_inclusive).")
    two_point_inclusive: bool = True
    reference_table: str | None = None
    reference_line_mm: float | None = Field(None, description="Age-based line at the age at scan.")
    distance_from_line_mm: float | None = Field(None, description="value_mm − reference line (mm).")


class StaticScoreResult(BaseModel):
    vi_points: int = Field(..., ge=0, le=2)
    ahw_points: int = Field(..., ge=0, le=2)
    tod_points: int = Field(..., ge=0, le=2)
    static_score: int = Field(..., ge=0, le=6)
    age_at_scan_weeks: float | None = None
    vi: MetricScore
    ahw: MetricScore
    tod: MetricScore


class ProgressionDeltas(BaseModel):
    """Worsening (current − prior) in mm; negative values are clamped to 0 for scoring."""

    delta_vi_mm: float
    delta_ahw_mm: float
    delta_tod_mm: float


class ProgressionScoreResult(BaseModel):
    vi_points: int = Field(..., ge=0, le=2)
    ahw_points: int = Field(..., ge=0, le=2)
    tod_points: int = Field(..., ge=0, le=2)
    progression_score: int = Field(..., ge=0, le=6)
    deltas_used: ProgressionDeltas


class ClinicalConcern(str, Enum):
    none = "none"
    mild = "mild"
    clear = "clear"


class ClinicalScoreInput(BaseModel):
    concern: ClinicalConcern = ClinicalConcern.none


class ClinicalScoreResult(BaseModel):
    clinical_modifier: int = Field(..., ge=0, le=2)


class NumicFlowScoreRequest(BaseModel):
    """One-shot scoring: current measurements, optional prior for progression, clinical modifier."""

    score_version: str = Field(default=DEFAULT_SCORE_VERSION, description=_SCORE_VERSION_DESCRIPTION)
    current: VentricularMeasurements
    age_at_scan_weeks: float | None = _age_field()
    prior: VentricularMeasurements | None = None
    clinical: ClinicalScoreInput = Field(default_factory=ClinicalScoreInput)


class NumicFlowScoreResponse(BaseModel):
    static: StaticScoreResult
    progression: ProgressionScoreResult | None
    clinical: ClinicalScoreResult
    numic_flow_score: int = Field(..., ge=0, le=14)
    risk_tier: RiskTier
    score_version: str
    rule_revision: str = Field(..., description="Revision that produced this result, e.g. numic_flow_levene@1.")


class StaticScoreRequest(BaseModel):
    score_version: str = Field(default=DEFAULT_SCORE_VERSION, description=_SCORE_VERSION_DESCRIPTION)
    measurements: VentricularMeasurements
    age_at_scan_weeks: float | None = _age_field()


class ProgressionScoreRequest(BaseModel):
    score_version: str = Field(default=DEFAULT_SCORE_VERSION, description=_SCORE_VERSION_DESCRIPTION)
    prior: VentricularMeasurements
    current: VentricularMeasurements


class ClinicalScoreRequest(BaseModel):
    score_version: str = Field(default=DEFAULT_SCORE_VERSION, description=_SCORE_VERSION_DESCRIPTION)
    clinical: ClinicalScoreInput
