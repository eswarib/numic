"""Smoke tests for scoring and overlay mapping."""

from fastapi.testclient import TestClient

from numic.main import app
from numic.measurement.pipeline import measurements_from_overlay
from numic.api.schemas.measurement import OverlayMetadata
from numic.api.schemas.scoring import (
    ClinicalConcern,
    ClinicalScoreInput,
    NumicFlowScoreRequest,
    VentricularMeasurements,
)
from numic.scoring import (
    compute_clinical_score,
    compute_progression_score,
    compute_static_score,
    get_rules,
    numic_flow_total,
    risk_tier,
)


def test_static_progression_clinical_sum() -> None:
    rules = get_rules("numic_flow_v1")
    current = VentricularMeasurements(
        vi_mm=11.0,
        vi_percentile=98.0,
        vi_p97_reference_mm=9.0,
        ahw_mm=7.0,
        tod_mm=26.0,
    )
    prior = VentricularMeasurements(
        vi_mm=9.0,
        vi_percentile=95.0,
        vi_p97_reference_mm=None,
        ahw_mm=5.0,
        tod_mm=22.0,
    )
    s = compute_static_score(current, rules)
    p = compute_progression_score(prior, current, rules)
    c = compute_clinical_score(ClinicalScoreInput(concern=ClinicalConcern.mild), rules)
    total = numic_flow_total(s.static_score, p.progression_score, c.clinical_modifier)
    assert 0 <= total <= 14
    assert risk_tier(total, rules) is not None


def test_vi_percentile_gate_differs_by_version() -> None:
    """96th percentile: v1 normal VI branch; v2_pre95 moderate VI branch."""
    m = VentricularMeasurements(
        vi_mm=10.0,
        vi_percentile=96.0,
        vi_p97_reference_mm=None,
        ahw_mm=5.0,
        tod_mm=24.0,
    )
    s_v1 = compute_static_score(m, get_rules("numic_flow_v1"))
    s_v2 = compute_static_score(m, get_rules("numic_flow_v2_pre95"))
    assert s_v1.vi_points == 0
    assert s_v2.vi_points == 1


def test_overlay_maps_to_measurements() -> None:
    o = OverlayMetadata(vi_mm=10.0, vi_percentile=96.0, ahw_mm=5.0, tod_mm=24.0)
    m = measurements_from_overlay(o)
    assert m.vi_mm == 10.0


def test_numic_flow_endpoint() -> None:
    client = TestClient(app)
    body = NumicFlowScoreRequest(
        current=VentricularMeasurements(
            vi_mm=10.0,
            vi_percentile=95.0,
            ahw_mm=5.0,
            tod_mm=24.0,
        ),
        clinical=ClinicalScoreInput(concern=ClinicalConcern.none),
    )
    r = client.post("/api/v1/score/numic-flow", json=body.model_dump())
    assert r.status_code == 200
    data = r.json()
    assert data["numic_flow_score"] == data["static"]["static_score"]
    assert data["progression"] is None
    assert data["score_version"] == "numic_flow_v1"


def test_unknown_score_version_422() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/score/versions")
    assert r.status_code == 200
    assert "numic_flow_v1" in r.json()["score_versions"]

    body = NumicFlowScoreRequest(
        score_version="does_not_exist",
        current=VentricularMeasurements(
            vi_mm=10.0,
            vi_percentile=95.0,
            ahw_mm=5.0,
            tod_mm=24.0,
        ),
    )
    r = client.post("/api/v1/score/numic-flow", json=body.model_dump())
    assert r.status_code == 422
