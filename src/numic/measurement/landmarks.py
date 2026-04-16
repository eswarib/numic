"""Coronal cUS calipers in pixel space → VI / AHW / TOD (mm).

Landmarks are *not* inferred from pixels here: they come from a trained model, a UI, or
an external viewer. This module only converts caliper endpoints to millimetres.

Convention: coordinates are **row, col** (vertical, horizontal) in pixel indices matching
``UltrasoundFrame.pixels`` indexing ``pixels[row, col]``.
"""

from __future__ import annotations

from dataclasses import dataclass

from numic.api.schemas.scoring import VentricularMeasurements
from numic.measurement.geometry import distance_mm_row_col


@dataclass(slots=True)
class CoronalLandmarkPixels:
    """Six endpoints for standard coronal linear measures (pixel row/col)."""

    ahw_left_row: float
    ahw_left_col: float
    ahw_right_row: float
    ahw_right_col: float
    tod_thalamus_row: float
    tod_thalamus_col: float
    tod_occipital_row: float
    tod_occipital_col: float
    vi_vent_left_row: float
    vi_vent_left_col: float
    vi_vent_right_row: float
    vi_vent_right_col: float


def measurements_from_coronal_landmarks(
    lm: CoronalLandmarkPixels,
    pixel_spacing_row_mm: float,
    pixel_spacing_col_mm: float,
    *,
    vi_percentile: float | None = None,
    vi_p97_reference_mm: float | None = None,
) -> VentricularMeasurements:
    """Convert coronal calipers to ``VentricularMeasurements``.

    Here ``vi_mm`` is the **ventricular width** segment between the two VI endpoints (mm),
    not a unitless index—align this with your centre’s VI definition if you use a ratio elsewhere.
    """
    ahw = distance_mm_row_col(
        lm.ahw_left_row,
        lm.ahw_left_col,
        lm.ahw_right_row,
        lm.ahw_right_col,
        pixel_spacing_row_mm,
        pixel_spacing_col_mm,
    )
    tod = distance_mm_row_col(
        lm.tod_thalamus_row,
        lm.tod_thalamus_col,
        lm.tod_occipital_row,
        lm.tod_occipital_col,
        pixel_spacing_row_mm,
        pixel_spacing_col_mm,
    )
    vi = distance_mm_row_col(
        lm.vi_vent_left_row,
        lm.vi_vent_left_col,
        lm.vi_vent_right_row,
        lm.vi_vent_right_col,
        pixel_spacing_row_mm,
        pixel_spacing_col_mm,
    )
    return VentricularMeasurements(
        vi_mm=vi,
        vi_percentile=vi_percentile,
        vi_p97_reference_mm=vi_p97_reference_mm,
        ahw_mm=ahw,
        tod_mm=tod,
    )
