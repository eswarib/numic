"""Pluggable extractors: image → ``VentricularMeasurements``."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from numic.api.schemas.scoring import VentricularMeasurements
from numic.measurement.frame import UltrasoundFrame


class MeasurementExtractionError(RuntimeError):
    """Raised when automatic extraction cannot run (missing model, spacing, etc.)."""


@runtime_checkable
class ImageMeasurementExtractor(Protocol):
    def extract(self, frame: UltrasoundFrame) -> VentricularMeasurements: ...


class UnconfiguredImageExtractor:
    """Default until an ONNX/Torch segmentation model is wired in."""

    def extract(self, frame: UltrasoundFrame) -> VentricularMeasurements:
        raise MeasurementExtractionError(
            "Automatic measurement from pixels is not configured. "
            "Integrate a segmentation model in a subclass, or use "
            "POST /api/v1/measurement/from-coronal-landmarks with caliper points, "
            "or POST /api/v1/measurement/from-overlay with precomputed mm values."
        )
