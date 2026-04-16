"""Operator-entered measurements (GUI or CLI) → ``PatientMeasurementRecord`` / ``VentricularMeasurements``."""

from __future__ import annotations

from numic.api.schemas.measurement import ManualMeasurementRequest, PatientMeasurementRecord
from numic.api.schemas.scoring import VentricularMeasurements


def patient_measurement_record_from_manual(req: ManualMeasurementRequest) -> PatientMeasurementRecord:
    """Build a full audit record including patient and acquisition context."""
    return PatientMeasurementRecord(
        patient=req.patient,
        context=req.context,
        measurements=VentricularMeasurements(
            vi_mm=req.vi_mm,
            vi_percentile=req.vi_percentile,
            vi_p97_reference_mm=req.vi_p97_reference_mm,
            ahw_mm=req.ahw_mm,
            tod_mm=req.tod_mm,
        ),
        entry_source=req.entry_source,
    )


def measurements_from_manual_entry(req: ManualMeasurementRequest) -> VentricularMeasurements:
    """Return only the ventricular metrics (for scoring pipelines)."""
    return patient_measurement_record_from_manual(req).measurements
