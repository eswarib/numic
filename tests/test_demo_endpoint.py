"""Demo combined measurement + scoring endpoint."""

from fastapi.testclient import TestClient

from numic.main import app


def test_demo_numic_flow_from_record() -> None:
    client = TestClient(app)
    body = {
        "record": {
            "patient": {
                "external_ref": "DEMO-1",
                "date_of_birth": "2025-04-01",
                "gestational_age_at_birth_weeks": 27,
                "gestational_age_at_birth_days": 3,
            },
            "context": {
                "measured_at": "2025-04-14T12:00:00+00:00",
                "measured_by": "demo",
                "clinical_notes": None,
            },
            "measurements": {"vi_mm": 10.0, "ahw_mm": 5.0, "tod_mm": 24.0},
            "entry_source": "cli",
        },
        "clinical": {"concern": "none"},
    }
    r = client.post("/api/v1/demo/numic-flow-from-record", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["patient"]["external_ref"] == "DEMO-1"
    assert "numic_flow_score" in data
    assert data["risk_tier"] in ("low", "moderate", "high")
    assert data["progression"] is None
    assert data["day_of_life"] == 13
    assert data["rule_revision"] == "numic_flow_levene@1"
    assert data["static"]["vi"]["reference_line_mm"] is not None


def test_demo_requires_birth_details_for_levene() -> None:
    client = TestClient(app)
    body = {
        "record": {
            "patient": {"external_ref": "DEMO-1"},
            "context": {"measured_at": "2025-04-14T12:00:00+00:00"},
            "measurements": {"vi_mm": 10.0, "ahw_mm": 5.0, "tod_mm": 24.0},
        }
    }
    r = client.post("/api/v1/demo/numic-flow-from-record", json=body)
    assert r.status_code == 422
    assert "date_of_birth" in r.json()["detail"]


def test_demo_rejects_scan_before_birth() -> None:
    client = TestClient(app)
    body = {
        "record": {
            "patient": {
                "external_ref": "DEMO-1",
                "date_of_birth": "2025-04-20",
                "gestational_age_at_birth_weeks": 28,
            },
            "context": {"measured_at": "2025-04-14T12:00:00+00:00"},
            "measurements": {"vi_mm": 10.0, "ahw_mm": 5.0, "tod_mm": 24.0},
        }
    }
    r = client.post("/api/v1/demo/numic-flow-from-record", json=body)
    assert r.status_code == 422
    assert "before the date of birth" in r.json()["detail"]


def test_demo_prior_must_match_patient() -> None:
    client = TestClient(app)
    ctx = {"measured_at": "2025-04-14T12:00:00+00:00", "measured_by": None, "clinical_notes": None}
    meas_a = {"vi_mm": 8.0, "ahw_mm": 5.0, "tod_mm": 22.0}
    meas_b = {**meas_a, "vi_mm": 9.5}
    body = {
        "record": {
            "patient": {"external_ref": "A"},
            "context": ctx,
            "measurements": meas_b,
        },
        "prior_record": {
            "patient": {"external_ref": "B"},
            "context": ctx,
            "measurements": meas_a,
        },
    }
    r = client.post("/api/v1/demo/numic-flow-from-record", json=body)
    assert r.status_code == 422
