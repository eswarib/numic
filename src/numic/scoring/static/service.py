"""Static score (0–6) from VI, AHW, TOD using a versioned rule bundle."""

from __future__ import annotations

from numic.api.schemas.scoring import StaticScoreResult, VentricularMeasurements
from numic.scoring.rules.models import NumicFlowRules, StaticRules


def score_vi(
    vi_mm: float,
    vi_percentile: float | None,
    vi_reference_mm: float | None,
    rules: StaticRules,
) -> int:
    """VI: below percentile gate → 0; else high if reference set and mm ≥ ref + delta; else 1."""
    if vi_percentile is None:
        raise ValueError("vi_percentile is required for VI static scoring")

    if vi_percentile < rules.vi_percentile_moderate_min:
        return 0

    if vi_reference_mm is not None and vi_mm >= vi_reference_mm + rules.vi_high_mm_above_reference:
        return 2

    return 1


def score_ahw(ahw_mm: float, rules: StaticRules) -> int:
    if ahw_mm < rules.ahw_normal_max_mm:
        return 0
    if ahw_mm <= rules.ahw_moderate_max_mm:
        return 1
    return 2


def score_tod(tod_mm: float, rules: StaticRules) -> int:
    if tod_mm < rules.tod_normal_max_mm:
        return 0
    if tod_mm < rules.tod_high_min_mm:
        return 1
    return 2


def compute_static_score(m: VentricularMeasurements, rules: NumicFlowRules) -> StaticScoreResult:
    s = rules.static
    vi = score_vi(m.vi_mm, m.vi_percentile, m.vi_p97_reference_mm, s)
    ahw = score_ahw(m.ahw_mm, s)
    tod = score_tod(m.tod_mm, s)
    return StaticScoreResult(
        vi_points=vi,
        ahw_points=ahw,
        tod_points=tod,
        static_score=vi + ahw + tod,
    )
