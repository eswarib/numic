"""ORM models aligned with the NumicFlow persistence schema (Postgres)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from numic.db.base import Base


class MeasurementRunStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RiskTier(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_ref: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    studies: Mapped[list[ImagingStudy]] = relationship(back_populates="patient")


class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    pacs_study_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    series_uid: Mapped[str | None] = mapped_column(String(128))
    modality: Mapped[str] = mapped_column(String(16), nullable=False, server_default="US")
    pacs_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="studies")
    measurement_runs: Mapped[list[MeasurementRun]] = relationship(back_populates="imaging_study")


class MeasurementRun(Base):
    __tablename__ = "measurement_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    imaging_study_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("imaging_studies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[MeasurementRunStatus] = mapped_column(
        Enum(MeasurementRunStatus, name="measurement_run_status", native_enum=False),
        nullable=False,
        server_default=MeasurementRunStatus.pending.value,
    )
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    imaging_study: Mapped[ImagingStudy] = relationship(back_populates="measurement_runs")
    measurement: Mapped[Measurement | None] = relationship(back_populates="measurement_run", uselist=False)


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    measurement_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("measurement_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    vi_mm: Mapped[float | None] = mapped_column(Float)
    ahw_mm: Mapped[float | None] = mapped_column(Float)
    tod_mm: Mapped[float | None] = mapped_column(Float)
    vi_percentile: Mapped[float | None] = mapped_column(Float)
    vi_p97_reference_mm: Mapped[float | None] = mapped_column(Float)
    static_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overlay_uri: Mapped[str | None] = mapped_column(Text)
    extras: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    measurement_run: Mapped[MeasurementRun] = relationship(back_populates="measurement")


class ProgressionEvaluation(Base):
    __tablename__ = "progression_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    prior_study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("imaging_studies.id", ondelete="CASCADE"))
    current_study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("imaging_studies.id", ondelete="CASCADE"))
    prior_measurement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("measurements.id", ondelete="CASCADE"))
    current_measurement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("measurements.id", ondelete="CASCADE"))
    interval_hours: Mapped[float] = mapped_column(Float, nullable=False)
    delta_vi_mm: Mapped[float] = mapped_column(Float, nullable=False)
    delta_ahw_mm: Mapped[float] = mapped_column(Float, nullable=False)
    delta_tod_mm: Mapped[float] = mapped_column(Float, nullable=False)
    progression_score: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_policy: Mapped[str] = mapped_column(String(64), nullable=False, server_default="prior_completed_study")
    score_version: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("current_study_id", "score_version", "interval_policy", name="uq_progression_current_ver"),
    )


class ClinicalAssessment(Base):
    __tablename__ = "clinical_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_uri: Mapped[str | None] = mapped_column(Text)
    source_checksum: Mapped[str | None] = mapped_column(String(128))
    clinical_modifier: Mapped[int] = mapped_column(Integer, nullable=False)
    flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    raw: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskReport(Base):
    __tablename__ = "risk_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    index_study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("imaging_studies.id", ondelete="CASCADE"))
    index_measurement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("measurements.id", ondelete="CASCADE"))
    clinical_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_assessments.id", ondelete="SET NULL")
    )
    progression_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("progression_evaluations.id", ondelete="SET NULL")
    )
    static_score: Mapped[int] = mapped_column(Integer, nullable=False)
    progression_score: Mapped[int] = mapped_column(Integer, nullable=False)
    clinical_modifier: Mapped[int] = mapped_column(Integer, nullable=False)
    numic_flow_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_tier: Mapped[RiskTier] = mapped_column(
        Enum(RiskTier, name="risk_tier", native_enum=False), nullable=False
    )
    score_version: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
