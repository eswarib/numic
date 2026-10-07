"""Scoring endpoints (static, progression, clinical, combined NumicFlow)."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from numic.api.schemas.measurement import (
    CoronalLandmarkCalipersRequest,
    ManualMeasurementRequest,
    OverlayMeasurementRequest,
    PatientMeasurementRecord,
    TabularImportResponse,
)
from numic.measurement.extractor import MeasurementExtractionError
from numic.measurement.landmarks import CoronalLandmarkPixels
from numic.measurement.pipeline import (
    extract_measurements_from_frame,
    load_ultrasound_frame_upload,
    measurements_from_coronal_landmark_pixels,
    measurements_from_manual,
    measurements_from_tabular_file,
    patient_record_from_overlay,
)
from numic.api.schemas.scoring import (
    ClinicalScoreRequest,
    ClinicalScoreResult,
    NumicFlowScoreRequest,
    NumicFlowScoreResponse,
    ProgressionScoreRequest,
    ProgressionScoreResult,
    StaticScoreRequest,
    StaticScoreResult,
    VentricularMeasurements,
)
from numic.scoring.clinical import compute_clinical_score
from numic.scoring.numic_flow import score_numic_flow
from numic.scoring.progression import compute_progression_score
from numic.scoring.rules import get_rules, list_rule_sets
from numic.scoring.static import compute_static_score

api_router = APIRouter()


def _rules_or_422(score_version: str):
    try:
        return get_rules(score_version)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@api_router.get("/score/versions")
def get_score_versions():
    rule_sets = list_rule_sets()
    return {
        "score_versions": [r.score_version for r in rule_sets],
        "rule_sets": [
            {"score_version": r.score_version, "revision": r.revision_id, "label": r.label}
            for r in rule_sets
        ],
    }


@api_router.post("/measurement/from-overlay", response_model=PatientMeasurementRecord)
def post_measurements_from_overlay(body: OverlayMeasurementRequest) -> PatientMeasurementRecord:
    """PACS/overlay mm values with patient identity and acquisition context."""
    return patient_record_from_overlay(body)


@api_router.post("/measurement/from-manual", response_model=PatientMeasurementRecord)
def post_measurements_from_manual(body: ManualMeasurementRequest) -> PatientMeasurementRecord:
    """Operator-entered VI / AHW / TOD (mm) with patient and scan context."""
    return measurements_from_manual(body)


@api_router.post("/measurement/from-manual-table", response_model=TabularImportResponse)
async def post_measurements_from_manual_table(file: UploadFile = File(...)) -> TabularImportResponse:
    """Bulk import: UTF-8 ``.csv`` or ``.xlsx``. Required per row: patient id, ``measured_at``, vi/ahw/tod.

    Columns (aliases): ``mrn``/``patient_id``, ``measured_at``, ``measured_by``, ``clinical_notes``,
    optional ``given_name``, ``family_name``, ``date_of_birth``, ``ga_at_birth_weeks``, ``ga_at_birth_days``.
    """
    data = await file.read()
    try:
        return measurements_from_tabular_file(data, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@api_router.post("/measurement/from-coronal-landmarks", response_model=PatientMeasurementRecord)
def post_measurements_from_coronal_landmarks(body: CoronalLandmarkCalipersRequest) -> PatientMeasurementRecord:
    """Derive VI/AHW/TOD (mm) from coronal calipers; includes patient and acquisition context."""
    lm = CoronalLandmarkPixels(
        ahw_left_row=body.ahw_left_row,
        ahw_left_col=body.ahw_left_col,
        ahw_right_row=body.ahw_right_row,
        ahw_right_col=body.ahw_right_col,
        tod_thalamus_row=body.tod_thalamus_row,
        tod_thalamus_col=body.tod_thalamus_col,
        tod_occipital_row=body.tod_occipital_row,
        tod_occipital_col=body.tod_occipital_col,
        vi_vent_left_row=body.vi_vent_left_row,
        vi_vent_left_col=body.vi_vent_left_col,
        vi_vent_right_row=body.vi_vent_right_row,
        vi_vent_right_col=body.vi_vent_right_col,
    )
    m = measurements_from_coronal_landmark_pixels(lm, body.pixel_spacing_row_mm, body.pixel_spacing_col_mm)
    return PatientMeasurementRecord(
        patient=body.patient,
        context=body.context,
        measurements=m,
        entry_source=body.entry_source or "landmarks",
    )


@api_router.post("/measurement/from-image", response_model=VentricularMeasurements)
async def post_measurements_from_image(file: UploadFile = File(...)) -> VentricularMeasurements:
    """Load a cUS frame (DICOM/PNG/JPEG) and run automatic extraction when configured.

    No patient/context here—attach those when persisting or use another entry path.
    """
    data = await file.read()
    frame = load_ultrasound_frame_upload(data, file.filename)
    try:
        return extract_measurements_from_frame(frame)
    except MeasurementExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@api_router.post("/score/static", response_model=StaticScoreResult)
def post_static(body: StaticScoreRequest) -> StaticScoreResult:
    rules = _rules_or_422(body.score_version)
    try:
        return compute_static_score(body.measurements, rules, body.age_at_scan_weeks)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@api_router.post("/score/progression", response_model=ProgressionScoreResult)
def post_progression(body: ProgressionScoreRequest) -> ProgressionScoreResult:
    rules = _rules_or_422(body.score_version)
    return compute_progression_score(body.prior, body.current, rules)


@api_router.post("/score/clinical", response_model=ClinicalScoreResult)
def post_clinical(body: ClinicalScoreRequest) -> ClinicalScoreResult:
    rules = _rules_or_422(body.score_version)
    return compute_clinical_score(body.clinical, rules)


@api_router.post("/score/numic-flow", response_model=NumicFlowScoreResponse)
def post_numic_flow(body: NumicFlowScoreRequest) -> NumicFlowScoreResponse:
    rules = _rules_or_422(body.score_version)
    try:
        return score_numic_flow(
            body.current,
            rules,
            age_at_scan_weeks=body.age_at_scan_weeks,
            prior=body.prior,
            clinical=body.clinical,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
