"""API request/response models for scoring endpoints (Pydantic)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class VentricularMeasurements(BaseModel):
    """Single-timepoint VI / AHW / TOD from cUS overlay or manual entry."""

    vi_mm: float = Field(..., description="Ventricular index (absolute mm as produced by your pipeline).")
    vi_percentile: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Percentile for GA; required to distinguish VI normal vs dilated.",
    )
    vi_p97_reference_mm: float | None = Field(
        None,
        description=(
            "Nomogram reference mm at the elevated-percentile line for this gestation (often p97). "
            "VI 'high' uses vi_mm ≥ reference + Δ, where Δ comes from score_version rules."
        ),
    )
    ahw_mm: float = Field(..., description="Anterior horn width (mm).")
    tod_mm: float = Field(..., description="Thalamo-occipital distance (mm).")


class StaticScoreResult(BaseModel):
    vi_points: int = Field(..., ge=0, le=2)
    ahw_points: int = Field(..., ge=0, le=2)
    tod_points: int = Field(..., ge=0, le=2)
    static_score: int = Field(..., ge=0, le=6)


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

    score_version: str = Field(
        default="numic_flow_v1",
        description="Which threshold bundle to use (e.g. numic_flow_v1, numic_flow_v2_pre95).",
    )
    current: VentricularMeasurements
    prior: VentricularMeasurements | None = None
    clinical: ClinicalScoreInput = Field(default_factory=ClinicalScoreInput)


class NumicFlowScoreResponse(BaseModel):
    static: StaticScoreResult
    progression: ProgressionScoreResult | None
    clinical: ClinicalScoreResult
    numic_flow_score: int = Field(..., ge=0, le=14)
    risk_tier: RiskTier
    score_version: str = "numic_flow_v1"


class StaticScoreRequest(BaseModel):
    score_version: str = Field(
        default="numic_flow_v1",
        description="Threshold bundle for static VI/AHW/TOD.",
    )
    measurements: VentricularMeasurements


class ProgressionScoreRequest(BaseModel):
    score_version: str = Field(default="numic_flow_v1", description="Threshold bundle for progression bands.")
    prior: VentricularMeasurements
    current: VentricularMeasurements


class ClinicalScoreRequest(BaseModel):
    score_version: str = Field(default="numic_flow_v1", description="Modifier mapping bundle.")
    clinical: ClinicalScoreInput
