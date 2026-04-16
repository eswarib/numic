"""In-memory cUS frame (pixels + physical calibration)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(slots=True)
class UltrasoundFrame:
    """Single 2D ultrasound frame (grayscale or RGB stored as H×W×C)."""

    pixels: np.ndarray
    """Image array, shape (H, W) or (H, W, 3), dtype typically uint8."""

    pixel_spacing_row_mm: float | None
    """Row direction: mm per pixel (DICOM PixelSpacing first value when available)."""

    pixel_spacing_col_mm: float | None
    """Column direction: mm per pixel (DICOM PixelSpacing second value)."""

    source_name: str | None = None
    metadata: dict[str, Any] | None = None

    def has_spacing(self) -> bool:
        return (
            self.pixel_spacing_row_mm is not None
            and self.pixel_spacing_col_mm is not None
            and self.pixel_spacing_row_mm > 0
            and self.pixel_spacing_col_mm > 0
        )
