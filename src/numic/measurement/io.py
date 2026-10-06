"""Load cUS frames from DICOM or common raster formats."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from numic.measurement.frame import UltrasoundFrame


def load_frame_from_path(path: Path) -> UltrasoundFrame:
    suffix = path.suffix.lower()
    if suffix in (".dcm", ".dic"):
        return _load_dicom_path(path)
    return _load_raster_path(path)


def load_frame_from_bytes(data: bytes, filename: str | None = None) -> UltrasoundFrame:
    name = (filename or "").lower()
    if name.endswith((".dcm", ".dic")) or _looks_like_dicom(data):
        return _load_dicom_bytes(data)
    return _load_pil_bytes(data)


def _looks_like_dicom(data: bytes) -> bool:
    return len(data) > 132 and data[128:132] == b"DICM"


def _load_dicom_path(path: Path) -> UltrasoundFrame:
    return _load_dicom_bytes(path.read_bytes())


def _load_dicom_bytes(data: bytes) -> UltrasoundFrame:
    import pydicom

    ds = pydicom.dcmread(BytesIO(data), force=True)
    arr = ds.pixel_array
    if arr.ndim == 3:
        # Multi-frame (T,H,W) or (H,W,C); heuristic: small last dim → channels, else time.
        if arr.shape[-1] <= 4 and arr.shape[0] > 4:
            arr = arr[..., 0]
        else:
            arr = arr[0]
    pixels = _normalize_to_uint8(arr)
    row_mm, col_mm = _dicom_pixel_spacing_mm(ds)
    meta = {"sop_class_uid": str(getattr(ds, "SOPClassUID", "")), "modality": str(getattr(ds, "Modality", ""))}
    return UltrasoundFrame(
        pixels=pixels,
        pixel_spacing_row_mm=row_mm,
        pixel_spacing_col_mm=col_mm,
        metadata=meta,
    )


def _dicom_pixel_spacing_mm(ds) -> tuple[float | None, float | None]:
    ps = getattr(ds, "PixelSpacing", None)
    if ps is None or len(ps) < 2:
        return None, None
    try:
        return float(ps[0]), float(ps[1])
    except (TypeError, ValueError):
        return None, None


def _normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
    if arr.dtype == np.uint8:
        return arr
    arr = arr.astype(np.float64)
    amin, amax = float(arr.min()), float(arr.max())
    if amax <= amin:
        return np.zeros(arr.shape, dtype=np.uint8)
    scaled = (arr - amin) / (amax - amin) * 255.0
    return scaled.astype(np.uint8)


def _load_raster_path(path: Path) -> UltrasoundFrame:
    return _load_pil_bytes(path.read_bytes(), source_name=path.name)


def _load_pil_bytes(data: bytes, source_name: str | None = None) -> UltrasoundFrame:
    im = Image.open(BytesIO(data))
    gray = im.convert("L")
    arr = np.asarray(gray)
    return UltrasoundFrame(
        pixels=arr,
        pixel_spacing_row_mm=None,
        pixel_spacing_col_mm=None,
        source_name=source_name,
        metadata={"format": im.format},
    )
