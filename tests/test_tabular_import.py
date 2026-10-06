"""CSV / xlsx manual measurement import."""

import io

from fastapi.testclient import TestClient
from openpyxl import Workbook

from numic.main import app
from numic.measurement.tabular_import import import_measurements_from_tabular


def test_import_csv_basic() -> None:
    csv_text = (
        "mrn,measured_at,measured_by,clinical_notes,vi,ahw,tod,vi_percentile\n"
        "P001,2025-04-14T10:00:00,dr_a,note one,8,6,24,90\n"
        "P002,2025-04-15T11:00:00,,,9,7,26,\n"
    )
    r = import_measurements_from_tabular(csv_text.encode("utf-8"), "batch.csv")
    assert len(r.rows) == 2
    assert r.rows[0].patient.external_ref == "P001"
    assert r.rows[0].context.measured_by == "dr_a"
    assert r.rows[0].context.clinical_notes == "note one"
    assert r.rows[0].measurements.vi_mm == 8.0
    assert r.rows[0].measurements.vi_percentile == 90.0
    assert r.rows[1].measurements.vi_percentile is None
    assert not r.skipped_rows


def test_import_csv_skips_bad_row() -> None:
    csv_text = (
        "vi_mm,ahw_mm,tod_mm,mrn,measured_at\n"
        "1,2,3,P1,2025-01-01T00:00:00\n"
        ",,,,\n"
        "4,5,6,P2,2025-01-02T00:00:00\n"
    )
    r = import_measurements_from_tabular(csv_text.encode("utf-8"), "x.csv")
    assert len(r.rows) == 2
    assert len(r.skipped_rows) == 1
    assert r.skipped_rows[0].row_number == 3


def test_import_csv_requires_measured_at() -> None:
    csv_text = "mrn,vi,ahw,tod\nP001,1,2,3\n"
    r = import_measurements_from_tabular(csv_text.encode("utf-8"), "x.csv")
    assert len(r.rows) == 0
    assert len(r.skipped_rows) == 1


def test_import_xlsx() -> None:
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.append(["patient_id", "measured_at", "VI_mm", "AHW", "TOD"])
    ws.append(["X1", datetime(2025, 6, 1, 8, 0, 0), 10.0, 5.0, 22.0])
    buf = io.BytesIO()
    wb.save(buf)
    r = import_measurements_from_tabular(buf.getvalue(), "data.xlsx")
    assert len(r.rows) == 1
    assert r.rows[0].patient.external_ref == "X1"
    assert r.rows[0].measurements.vi_mm == 10.0


def test_xls_rejected() -> None:
    try:
        import_measurements_from_tabular(b"dummy", "old.xls")
    except ValueError as e:
        assert "xls" in str(e).lower()
    else:
        raise AssertionError("expected ValueError")


def test_endpoint_manual_table() -> None:
    client = TestClient(app)
    body = (
        b"mrn,measured_at,vi,ahw,tod\n"
        b"P9,2025-04-01T12:00:00,1,2,3\n"
    )
    r = client.post(
        "/api/v1/measurement/from-manual-table",
        files={"file": ("t.csv", body, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["rows"]) == 1
    assert data["rows"][0]["measurements"]["vi_mm"] == 1.0
    assert data["rows"][0]["patient"]["external_ref"] == "P9"
