"""Public demo API contracts. Requests reject unknown fields and have no free-text inputs (DEMO-F10)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from numic.api.schemas.scoring import ClinicalConcern, NumicFlowScoreResponse, RiskTier


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BabyCreate(_Strict):
    date_of_birth: date
    ga_weeks: int = Field(..., ge=22, le=42, description="Gestational age at birth, completed weeks.")
    ga_days: int = Field(0, ge=0, le=6, description="Gestational age at birth, extra days.")


class ScanCreate(_Strict):
    measured_at: datetime = Field(..., description="Scan date and time (ISO-8601, with offset).")
    vi_left_mm: float = Field(..., ge=0, le=40)
    vi_right_mm: float = Field(..., ge=0, le=40)
    ahw_mm: float = Field(..., ge=0, le=40)
    tod_mm: float = Field(..., ge=0, le=60)
    clinical_concern: ClinicalConcern = ClinicalConcern.none


class Assessment(BaseModel):
    status: Literal["scored", "not_scored"]
    message: str | None = Field(None, description="Why the scan was not scored (e.g. outside chart range).")
    risk_tier: RiskTier | None = None
    numic_flow_score: int | None = None
    result: NumicFlowScoreResponse | None = None
    reasons: list[str] = []
    rule_revision: str
    compared_with_scan_id: str | None = None


class ScanOut(BaseModel):
    id: str
    measured_at: datetime
    day_of_life: int | None
    age_weeks: float | None
    age_label: str | None
    vi_left_mm: float
    vi_right_mm: float
    vi_mm: float = Field(..., description="Larger of left and right; this is the VI that is scored.")
    ahw_mm: float
    tod_mm: float
    clinical_concern: ClinicalConcern
    read_only: bool = Field(..., description="Seed scans are shared and cannot be changed.")
    assessment: Assessment


class ReferenceLine(BaseModel):
    metric: Literal["vi", "ahw", "tod"]
    kind: Literal["reference_line", "fixed"]
    label: str
    verified: bool | None = None
    one_point_offset_mm: float | None = None
    two_point_offset_mm: float | None = None
    points: list[tuple[float, float]] = Field(
        [], description="(age in weeks, line in mm) for reference lines."
    )
    one_point_mm: float | None = None
    two_point_mm: float | None = None


class RuleSetInfo(BaseModel):
    score_version: str
    revision: str
    label: str
    low_max: int
    moderate_max: int
    lines: list[ReferenceLine]


class BabySummary(BaseModel):
    id: str
    read_only: bool
    story: str | None = None
    date_of_birth: date
    ga_weeks: int
    ga_days: int
    ga_label: str
    scan_count: int
    latest_scan_at: datetime | None = None
    latest_age_label: str | None = None
    latest_status: Literal["scored", "not_scored"] | None = None
    latest_risk_tier: RiskTier | None = None
    latest_score: int | None = None


class BabyDetail(BabySummary):
    scans: list[ScanOut]
    can_add_scan: bool
    rule_set: RuleSetInfo


class BabyList(BaseModel):
    babies: list[BabySummary]
    sandbox_baby_count: int
    max_babies: int
    rule_set: RuleSetInfo
