"""Demo-only API contracts (single-call measurement record → NumicFlow score)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from numic.api.schemas.measurement import PatientInfo, PatientMeasurementRecord, MeasurementContext
from numic.api.schemas.scoring import (
    ClinicalScoreInput,
    ClinicalScoreResult,
    ProgressionScoreResult,
    RiskTier,
    StaticScoreResult,
    VentricularMeasurements,
)


class DemoNumicFlowFromRecordRequest(BaseModel):
    """Convenience payload for demos: full current record + optional prior record + clinical."""

    score_version: str = Field(
        default="numic_flow_v1",
        description="Threshold bundle (same as production scoring).",
    )
    record: PatientMeasurementRecord
    prior_record: PatientMeasurementRecord | None = Field(
        None,
        description="Optional earlier timepoint; progression uses prior_record.measurements vs record.measurements.",
    )
    clinical: ClinicalScoreInput = Field(default_factory=ClinicalScoreInput)


class DemoNumicFlowFromRecordResponse(BaseModel):
    """Echo patient/context plus NumicFlow breakdown (demo / prototyping only)."""

    patient: PatientInfo
    context: MeasurementContext
    entry_source: str | None = None
    measurements: VentricularMeasurements
    static: StaticScoreResult
    progression: ProgressionScoreResult | None
    clinical: ClinicalScoreResult
    numic_flow_score: int = Field(..., ge=0, le=14)
    risk_tier: RiskTier
    score_version: str
