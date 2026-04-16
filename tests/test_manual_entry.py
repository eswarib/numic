"""Manual / operator measurement path."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from numic.api.schemas.measurement import ManualMeasurementRequest, MeasurementContext, PatientInfo
from numic.main import app
from numic.measurement.manual_entry import measurements_from_manual_entry, patient_measurement_record_from_manual
from numic.cli.measure import main as cli_main


def _ctx():
    return MeasurementContext(
        measured_at=datetime(2025, 4, 14, 10, 30, tzinfo=timezone.utc),
        measured_by="sono1",
        clinical_notes="IVH grade II; clinically stable.",
    )


def _patient():
    return PatientInfo(
        external_ref="MRN-1001",
        given_name="Baby",
        family_name="Test",
        gestational_age_weeks=28.0,
    )


def test_manual_entry_to_ventricular() -> None:
    req = ManualMeasurementRequest(
        patient=_patient(),
        context=_ctx(),
        vi_mm=8.0,
        ahw_mm=6.5,
        tod_mm=24.0,
        vi_percentile=90.0,
        entry_source="gui",
    )
    m = measurements_from_manual_entry(req)
    assert m.vi_mm == 8.0
    assert m.ahw_mm == 6.5
    assert m.tod_mm == 24.0
    assert m.vi_percentile == 90.0


def test_patient_measurement_record() -> None:
    req = ManualMeasurementRequest(
        patient=_patient(),
        context=_ctx(),
        vi_mm=7.0,
        ahw_mm=5.0,
        tod_mm=22.0,
    )
    rec = patient_measurement_record_from_manual(req)
    assert rec.patient.external_ref == "MRN-1001"
    assert rec.context.measured_by == "sono1"
    assert rec.measurements.vi_mm == 7.0


def test_from_manual_endpoint() -> None:
    client = TestClient(app)
    body = {
        "patient": {
            "external_ref": "EPI-9",
            "given_name": "A",
            "family_name": "B",
        },
        "context": {
            "measured_at": "2025-04-14T12:00:00+00:00",
            "measured_by": "cli-test",
            "clinical_notes": None,
        },
        "vi_mm": 7.0,
        "ahw_mm": 5.0,
        "tod_mm": 22.0,
        "entry_source": "cli",
    }
    r = client.post("/api/v1/measurement/from-manual", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["measurements"]["vi_mm"] == 7.0
    assert data["patient"]["external_ref"] == "EPI-9"
    assert data["context"]["measured_by"] == "cli-test"


def test_cli_measure_json(capsys) -> None:
    code = cli_main(
        [
            "--patient-ref",
            "P1",
            "--measured-at",
            "2025-01-15T10:00:00",
            "--vi",
            "1",
            "--ahw",
            "2",
            "--tod",
            "3",
            "--vi-percentile",
            "50",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert '"vi_mm":1' in out.replace(" ", "") or '"vi_mm": 1' in out
