"""API request bodies: cUS / PACS overlay metadata (Pydantic)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from numic.api.schemas.scoring import VentricularMeasurements


class PatientInfo(BaseModel):
    """Who the scan / calipers belong to."""

    external_ref: str = Field(
        ...,
        min_length=1,
        description="Hospital patient key: MRN, episode ID, or other stable identifier.",
    )
    given_name: str | None = Field(None, max_length=128)
    family_name: str | None = Field(None, max_length=128)
    date_of_birth: date | None = None
    gestational_age_weeks: float | None = Field(
        None,
        ge=10.0,
        le=45.0,
        description="Gestational age at scan when relevant (weeks).",
    )


class MeasurementContext(BaseModel):
    """When the measurement was taken, by whom, and free-text clinical notes."""

    measured_at: datetime = Field(
        ...,
        description="Date/time of the cUS or caliper read (timezone-aware ISO-8601 recommended).",
    )
    measured_by: str | None = Field(
        None,
        max_length=256,
        description="Sonographer, clinician, or system user who performed the measurement.",
    )
    clinical_notes: str | None = Field(
        None,
        max_length=20_000,
        description="Free-text clinical context (e.g. IVH grade, instability, concurrent issues).",
    )


class PatientMeasurementRecord(BaseModel):
    """Full audit row: patient + context + ventricular metrics for scoring."""

    patient: PatientInfo
    context: MeasurementContext
    measurements: VentricularMeasurements
    entry_source: Literal["gui", "cli", "other", "tabular", "overlay", "landmarks", "image"] | None = None


class ManualMeasurementRequest(BaseModel):
    """VI / AHW / TOD from a GUI or CLI with mandatory patient and measurement context."""

    patient: PatientInfo
    context: MeasurementContext
    vi_mm: float = Field(..., ge=0, description="Ventricular index or width per your protocol (mm).")
    ahw_mm: float = Field(..., ge=0, description="Anterior horn width (mm).")
    tod_mm: float = Field(..., ge=0, description="Thalamo-occipital distance (mm).")
    vi_percentile: float | None = Field(None, ge=0, le=100)
    vi_p97_reference_mm: float | None = Field(
        None, description="Nomogram reference mm at the elevated VI percentile for GA."
    )
    entry_source: Literal["gui", "cli", "other"] | None = Field(
        None, description="Where the values were captured (audit trail)."
    )


class CoronalLandmarkCalipersRequest(BaseModel):
    """Coronal calipers in pixel row/col plus patient/context for the same acquisition."""

    patient: PatientInfo
    context: MeasurementContext
    entry_source: Literal["gui", "cli", "other", "landmarks"] | None = None

    pixel_spacing_row_mm: float = Field(..., gt=0, description="mm per pixel in row direction")
    pixel_spacing_col_mm: float = Field(..., gt=0, description="mm per pixel in column direction")
    vi_percentile: float | None = Field(None, ge=0, le=100)
    vi_p97_reference_mm: float | None = None

    ahw_left_row: float
    ahw_left_col: float
    ahw_right_row: float
    ahw_right_col: float
    tod_thalamus_row: float
    tod_thalamus_col: float
    tod_occipital_row: float
    tod_occipital_col: float
    vi_vent_left_row: float
    vi_vent_left_col: float
    vi_vent_right_row: float
    vi_vent_right_col: float


class OverlayMetadata(BaseModel):
    """Numeric overlay output only (no patient)—use ``OverlayMeasurementRequest`` for API uploads."""

    vi_mm: float = Field(..., description="Ventricular index (mm).")
    vi_percentile: float | None = Field(None, ge=0, le=100)
    vi_p97_reference_mm: float | None = Field(
        None, description="97th percentile VI in mm for GA (for VI 'high' rule)."
    )
    ahw_mm: float = Field(..., description="Anterior horn width (mm).")
    tod_mm: float = Field(..., description="Thalamo-occipital distance (mm).")


class OverlayMeasurementRequest(BaseModel):
    """Overlay/PACS mm values with patient and acquisition context."""

    patient: PatientInfo
    context: MeasurementContext
    overlay: OverlayMetadata
    entry_source: Literal["overlay", "pacs", "other"] | None = "overlay"


class TabularImportSkippedRow(BaseModel):
    """A data row that could not be converted (missing/invalid fields)."""

    row_number: int = Field(..., description="1-based row index (row 1 = header).")
    reason: str


class TabularImportRowOut(BaseModel):
    """One successfully parsed row from a CSV / Excel manual import."""

    row_number: int
    patient: PatientInfo
    context: MeasurementContext
    measurements: VentricularMeasurements
    entry_source: Literal["tabular"] = "tabular"


class TabularImportResponse(BaseModel):
    """Result of uploading a measurement table (.csv or .xlsx)."""

    rows: list[TabularImportRowOut]
    skipped_rows: list[TabularImportSkippedRow]
