"""Pixel ↔ millimetre geometry (anisotropic spacing)."""

from __future__ import annotations

import math


def distance_mm_row_col(
    row0: float,
    col0: float,
    row1: float,
    col1: float,
    pixel_spacing_row_mm: float,
    pixel_spacing_col_mm: float,
) -> float:
    """Euclidean distance in mm given row/col pixel indices and spacing (mm per pixel)."""
    dr = (row0 - row1) * pixel_spacing_row_mm
    dc = (col0 - col1) * pixel_spacing_col_mm
    return math.hypot(dr, dc)
