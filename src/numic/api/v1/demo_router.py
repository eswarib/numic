"""Demo routes: shortcuts for prototyping (not a substitute for production orchestration)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from numic.api.schemas.demo import DemoNumicFlowFromRecordRequest, DemoNumicFlowFromRecordResponse
from numic.api.schemas.measurement import PatientMeasurementRecord
from numic.core.config import get_settings
from numic.scoring.nomogram import AgeAtScan, age_at_scan
from numic.scoring.numic_flow import score_numic_flow
from numic.scoring.rules import get_rules

demo_router = APIRouter(prefix="/demo", tags=["demo"])


def _age(record: PatientMeasurementRecord, needs_age: bool) -> AgeAtScan | None:
    p = record.patient
    if p.date_of_birth is None or p.gestational_age_at_birth_weeks is None:
        if needs_age:
            raise ValueError(
                "patient.date_of_birth and patient.gestational_age_at_birth_weeks are required "
                "for age-based rule sets"
            )
        return None
    return age_at_scan(
        p.date_of_birth,
        p.gestational_age_at_birth_weeks,
        p.gestational_age_at_birth_days,
        record.context.measured_at,
        get_settings().scan_day_timezone,
    )


@demo_router.post(
    "/numic-flow-from-record",
    response_model=DemoNumicFlowFromRecordResponse,
    summary="Demo: patient record(s) → NumicFlow score in one call",
)
def demo_numic_flow_from_record(body: DemoNumicFlowFromRecordRequest) -> DemoNumicFlowFromRecordResponse:
    """Run static + progression (if ``prior_record``) + clinical on embedded measurements.

    Age at scan is worked out from the patient's date of birth, gestational age at birth and
    ``context.measured_at``. Intended for demos and quick UI wiring.
    """
    prior = body.prior_record
    if prior is not None:
        if prior.patient.external_ref.strip() != body.record.patient.external_ref.strip():
            raise HTTPException(
                status_code=422,
                detail="prior_record.patient.external_ref must match record.patient.external_ref",
            )
        if prior.context.measured_at >= body.record.context.measured_at:
            raise HTTPException(status_code=422, detail="prior_record must be earlier than record")

    try:
        rules = get_rules(body.score_version)
        age = _age(body.record, rules.static.needs_age)
        if prior is not None:
            _age(prior, False)  # reject a prior scan dated before the birth
        result = score_numic_flow(
            body.record.measurements,
            rules,
            age_at_scan_weeks=None if age is None else age.age_weeks,
            prior=None if prior is None else prior.measurements,
            clinical=body.clinical,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return DemoNumicFlowFromRecordResponse(
        patient=body.record.patient,
        context=body.record.context,
        entry_source=body.record.entry_source,
        measurements=body.record.measurements,
        day_of_life=None if age is None else age.day_of_life,
        age_at_scan_weeks=None if age is None else age.age_weeks,
        **result.model_dump(),
    )
