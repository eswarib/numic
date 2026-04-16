"""Demo routes: shortcuts for prototyping (not a substitute for production orchestration)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from numic.api.schemas.demo import DemoNumicFlowFromRecordRequest, DemoNumicFlowFromRecordResponse
from numic.scoring.aggregate import numic_flow_total, risk_tier
from numic.scoring.clinical import compute_clinical_score
from numic.scoring.progression import compute_progression_score
from numic.scoring.rules import get_rules
from numic.scoring.static import compute_static_score

demo_router = APIRouter(prefix="/demo", tags=["demo"])


def _rules_or_422(score_version: str):
    try:
        return get_rules(score_version)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@demo_router.post(
    "/numic-flow-from-record",
    response_model=DemoNumicFlowFromRecordResponse,
    summary="Demo: patient record(s) → NumicFlow score in one call",
)
async def demo_numic_flow_from_record(
    body: DemoNumicFlowFromRecordRequest,
) -> DemoNumicFlowFromRecordResponse:
    """Run static + progression (if ``prior_record``) + clinical on embedded measurements.

    Intended for demos and quick UI wiring. Production flows may keep separate measurement persistence and scoring steps.
    """
    if body.prior_record is not None:
        if (
            body.prior_record.patient.external_ref.strip()
            != body.record.patient.external_ref.strip()
        ):
            raise HTTPException(
                status_code=422,
                detail="prior_record.patient.external_ref must match record.patient.external_ref",
            )

    rules = _rules_or_422(body.score_version)
    current = body.record.measurements
    prior = body.prior_record.measurements if body.prior_record else None

    async def _static():
        return await asyncio.to_thread(compute_static_score, current, rules)

    async def _clinical():
        return await asyncio.to_thread(compute_clinical_score, body.clinical, rules)

    async def _prog():
        if prior is None:
            return None
        return await asyncio.to_thread(compute_progression_score, prior, current, rules)

    try:
        static, clinical_result, prog = await asyncio.gather(_static(), _clinical(), _prog())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    prog_score = 0 if prog is None else prog.progression_score
    total = numic_flow_total(static.static_score, prog_score, clinical_result.clinical_modifier)

    return DemoNumicFlowFromRecordResponse(
        patient=body.record.patient,
        context=body.record.context,
        entry_source=body.record.entry_source,
        measurements=current,
        static=static,
        progression=prog,
        clinical=clinical_result,
        numic_flow_score=total,
        risk_tier=risk_tier(total, rules),
        score_version=rules.score_version,
    )
