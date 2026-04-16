"""Measurement I/O and landmark geometry."""

import io

from fastapi.testclient import TestClient
from PIL import Image

from numic.main import app
from numic.measurement.geometry import distance_mm_row_col
from numic.measurement.landmarks import CoronalLandmarkPixels, measurements_from_coronal_landmarks


def test_distance_mm_anisotropic() -> None:
    d = distance_mm_row_col(0.0, 0.0, 0.0, 10.0, pixel_spacing_row_mm=0.5, pixel_spacing_col_mm=0.3)
    assert abs(d - 3.0) < 1e-9


def test_coronal_landmarks_to_measurements() -> None:
    lm = CoronalLandmarkPixels(
        ahw_left_row=0.0,
        ahw_left_col=0.0,
        ahw_right_row=0.0,
        ahw_right_col=10.0,
        tod_thalamus_row=0.0,
        tod_thalamus_col=0.0,
        tod_occipital_row=5.0,
        tod_occipital_col=0.0,
        vi_vent_left_row=0.0,
        vi_vent_left_col=0.0,
        vi_vent_right_row=0.0,
        vi_vent_right_col=4.0,
    )
    m = measurements_from_coronal_landmarks(lm, 1.0, 1.0, vi_percentile=50.0)
    assert m.ahw_mm == 10.0
    assert m.tod_mm == 5.0
    assert m.vi_mm == 4.0
    assert m.vi_percentile == 50.0


def test_from_image_returns_422_until_extractor_configured() -> None:
    im = Image.new("L", (64, 64), color=128)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    client = TestClient(app)
    r = client.post(
        "/api/v1/measurement/from-image",
        files={"file": ("test.png", buf.getvalue(), "image/png")},
    )
    assert r.status_code == 422
    assert "not configured" in r.json()["detail"].lower()


def test_from_coronal_landmarks_endpoint() -> None:
    client = TestClient(app)
    body = {
        "patient": {"external_ref": "LM-1"},
        "context": {
            "measured_at": "2025-04-14T09:00:00+00:00",
            "measured_by": "landmark-ui",
            "clinical_notes": "Coronal plane QC ok",
        },
        "pixel_spacing_row_mm": 0.1,
        "pixel_spacing_col_mm": 0.1,
        "ahw_left_row": 0,
        "ahw_left_col": 0,
        "ahw_right_row": 0,
        "ahw_right_col": 10,
        "tod_thalamus_row": 0,
        "tod_thalamus_col": 0,
        "tod_occipital_row": 8,
        "tod_occipital_col": 0,
        "vi_vent_left_row": 0,
        "vi_vent_left_col": 0,
        "vi_vent_right_row": 0,
        "vi_vent_right_col": 5,
    }
    r = client.post("/api/v1/measurement/from-coronal-landmarks", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["measurements"]["ahw_mm"] == 1.0
    assert data["measurements"]["tod_mm"] == 0.8
    assert data["measurements"]["vi_mm"] == 0.5
    assert data["patient"]["external_ref"] == "LM-1"
    assert data["context"]["measured_by"] == "landmark-ui"
