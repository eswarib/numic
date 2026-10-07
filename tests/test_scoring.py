"""Scoring layers with the numic_flow_levene rule set."""

import pytest
from fastapi.testclient import TestClient

from numic.api.schemas.measurement import OverlayMetadata
from numic.api.schemas.scoring import (
    ClinicalConcern,
    ClinicalScoreInput,
    NumicFlowScoreRequest,
    VentricularMeasurements,
)
from numic.main import app
from numic.measurement.pipeline import measurements_from_overlay
from numic.scoring import (
    compute_clinical_score,
    compute_progression_score,
    compute_static_score,
    get_rules,
    numic_flow_total,
    risk_tier,
)
from numic.scoring.nomogram import OutOfChartRangeError, get_table
from numic.scoring.static import AgeRequiredError


def _m(vi: float, ahw: float = 5.0, tod: float = 22.0) -> VentricularMeasurements:
    return VentricularMeasurements(vi_mm=vi, ahw_mm=ahw, tod_mm=tod)


def test_static_progression_clinical_sum() -> None:
    rules = get_rules("numic_flow_levene")
    current = _m(13.0, ahw=7.0, tod=26.0)
    prior = _m(11.0, ahw=5.0, tod=22.0)
    s = compute_static_score(current, rules, 30.0)
    p = compute_progression_score(prior, current, rules)
    c = compute_clinical_score(ClinicalScoreInput(concern=ClinicalConcern.mild), rules)
    total = numic_flow_total(s.static_score, p.progression_score, c.clinical_modifier)
    # VI 1 (above line 11.9), AHW 1, TOD 1; progression VI 2 + AHW 2 + TOD 2; mild 1
    assert (s.static_score, p.progression_score, c.clinical_modifier) == (3, 6, 1)
    assert risk_tier(total, rules).value == "high"


def test_vi_uses_levene_line_at_age() -> None:
    rules = get_rules()
    line = get_table("levene_vi_p97").line_at(30.0)
    assert compute_static_score(_m(line - 0.1), rules, 30.0).vi_points == 0
    assert compute_static_score(_m(line), rules, 30.0).vi_points == 1
    assert compute_static_score(_m(line + 3.9), rules, 30.0).vi_points == 1
    assert compute_static_score(_m(line + 4.0), rules, 30.0).vi_points == 2
    # the same VI is below the line at an older age
    assert compute_static_score(_m(line + 0.5), rules, 34.0).vi_points == 0


def test_static_result_explains_reference_values() -> None:
    s = compute_static_score(_m(13.0), get_rules(), 30.0)
    assert s.age_at_scan_weeks == 30.0
    assert s.vi.reference_table == "levene_vi_p97"
    assert s.vi.reference_line_mm == pytest.approx(11.9)
    assert s.vi.distance_from_line_mm == pytest.approx(1.1)
    assert s.ahw.kind == "fixed"


def test_fixed_ahw_and_tod_cut_offs() -> None:
    rules = get_rules()
    pts = lambda ahw, tod: (  # noqa: E731
        compute_static_score(_m(5.0, ahw, tod), rules, 30.0).ahw_points,
        compute_static_score(_m(5.0, ahw, tod), rules, 30.0).tod_points,
    )
    assert pts(5.9, 24.9) == (0, 0)
    assert pts(6.0, 25.0) == (1, 1)
    assert pts(10.0, 29.9) == (1, 1)
    assert pts(10.1, 30.0) == (2, 2)


def test_age_required_and_out_of_range() -> None:
    rules = get_rules()
    with pytest.raises(AgeRequiredError):
        compute_static_score(_m(10.0), rules, None)
    with pytest.raises(OutOfChartRangeError):
        compute_static_score(_m(10.0), rules, 24.5)


def test_overlay_maps_to_measurements() -> None:
    o = OverlayMetadata(vi_mm=10.0, ahw_mm=5.0, tod_mm=24.0)
    m = measurements_from_overlay(o)
    assert m.vi_mm == 10.0


def test_numic_flow_endpoint() -> None:
    client = TestClient(app)
    body = NumicFlowScoreRequest(
        current=_m(10.0, 5.0, 24.0),
        age_at_scan_weeks=30.0,
        clinical=ClinicalScoreInput(concern=ClinicalConcern.none),
    )
    r = client.post("/api/v1/score/numic-flow", json=body.model_dump(mode="json"))
    assert r.status_code == 200
    data = r.json()
    assert data["numic_flow_score"] == data["static"]["static_score"]
    assert data["progression"] is None
    assert data["score_version"] == "numic_flow_levene"
    assert data["rule_revision"] == "numic_flow_levene@1"


def test_numic_flow_endpoint_out_of_range_422() -> None:
    client = TestClient(app)
    body = {"current": {"vi_mm": 10.0, "ahw_mm": 5.0, "tod_mm": 24.0}, "age_at_scan_weeks": 24.5}
    r = client.post("/api/v1/score/numic-flow", json=body)
    assert r.status_code == 422
    assert "outside" in r.json()["detail"]


def test_versions_list_levene_only() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/score/versions")
    assert r.status_code == 200
    data = r.json()
    assert data["score_versions"] == ["numic_flow_levene"]
    assert data["rule_sets"][0]["revision"] == "numic_flow_levene@1"


@pytest.mark.parametrize(
    "version", ["does_not_exist", "numic_flow_v1", "numic_flow_v2_pre95", "numic_flow_levene@9"]
)
def test_unknown_or_retired_score_version_422(version: str) -> None:
    client = TestClient(app)
    body = {
        "score_version": version,
        "current": {"vi_mm": 10.0, "ahw_mm": 5.0, "tod_mm": 24.0},
        "age_at_scan_weeks": 30.0,
    }
    r = client.post("/api/v1/score/numic-flow", json=body)
    assert r.status_code == 422
    assert "numic_flow_levene@1" in r.json()["detail"]


def test_pinned_revision_accepted() -> None:
    assert get_rules("numic_flow_levene@1").revision_id == "numic_flow_levene@1"
