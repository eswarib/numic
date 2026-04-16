"""Measurement path: overlay metadata, coronal calipers, or (future) automatic image extraction."""

from __future__ import annotations

from pathlib import Path

from numic.api.schemas.measurement import (
    ManualMeasurementRequest,
    OverlayMeasurementRequest,
    OverlayMetadata,
    PatientMeasurementRecord,
    TabularImportResponse,
)
from numic.api.schemas.scoring import VentricularMeasurements
from numic.measurement.manual_entry import patient_measurement_record_from_manual
from numic.measurement.tabular_import import import_measurements_from_tabular
from numic.measurement.extractor import (
    ImageMeasurementExtractor,
    MeasurementExtractionError,
    UnconfiguredImageExtractor,
)
from numic.measurement.frame import UltrasoundFrame
from numic.measurement.io import load_frame_from_bytes, load_frame_from_path
from numic.measurement.landmarks import CoronalLandmarkPixels, measurements_from_coronal_landmarks


def measurements_from_manual(req: ManualMeasurementRequest) -> PatientMeasurementRecord:
    return patient_measurement_record_from_manual(req)


def patient_record_from_overlay(req: OverlayMeasurementRequest) -> PatientMeasurementRecord:
    return PatientMeasurementRecord(
        patient=req.patient,
        context=req.context,
        measurements=ventricular_measurements_from_overlay(req.overlay),
        entry_source=req.entry_source,
    )


def ventricular_measurements_from_overlay(overlay: OverlayMetadata) -> VentricularMeasurements:
    return VentricularMeasurements(
        vi_mm=overlay.vi_mm,
        vi_percentile=overlay.vi_percentile,
        vi_p97_reference_mm=overlay.vi_p97_reference_mm,
        ahw_mm=overlay.ahw_mm,
        tod_mm=overlay.tod_mm,
    )


def measurements_from_overlay(overlay: OverlayMetadata) -> VentricularMeasurements:
    """Backward-compatible alias for numeric overlay metadata only."""
    return ventricular_measurements_from_overlay(overlay)


def measurements_from_tabular_file(content: bytes, filename: str) -> TabularImportResponse:
    """Parse ``.csv`` or ``.xlsx`` exported from a GUI / spreadsheet into measurement rows."""
    return import_measurements_from_tabular(content, filename)


def load_ultrasound_frame(path: Path) -> UltrasoundFrame:
    return load_frame_from_path(path)


def load_ultrasound_frame_upload(data: bytes, filename: str | None = None) -> UltrasoundFrame:
    return load_frame_from_bytes(data, filename)


def extract_measurements_from_frame(
    frame: UltrasoundFrame,
    extractor: ImageMeasurementExtractor | None = None,
) -> VentricularMeasurements:
    ext = extractor or UnconfiguredImageExtractor()
    return ext.extract(frame)


def measurements_from_coronal_landmark_pixels(
    lm: CoronalLandmarkPixels,
    pixel_spacing_row_mm: float,
    pixel_spacing_col_mm: float,
    *,
    vi_percentile: float | None = None,
    vi_p97_reference_mm: float | None = None,
) -> VentricularMeasurements:
    return measurements_from_coronal_landmarks(
        lm,
        pixel_spacing_row_mm,
        pixel_spacing_col_mm,
        vi_percentile=vi_percentile,
        vi_p97_reference_mm=vi_p97_reference_mm,
    )


__all__ = [
    "CoronalLandmarkPixels",
    "MeasurementExtractionError",
    "UnconfiguredImageExtractor",
    "extract_measurements_from_frame",
    "load_ultrasound_frame",
    "load_ultrasound_frame_upload",
    "measurements_from_coronal_landmark_pixels",
    "measurements_from_manual",
    "measurements_from_overlay",
    "measurements_from_tabular_file",
    "patient_record_from_overlay",
    "ventricular_measurements_from_overlay",
]
