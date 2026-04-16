"""Progression score (0–6) from mm change vs prior timepoint (versioned rules)."""

from __future__ import annotations

from numic.api.schemas.scoring import (
    ProgressionDeltas,
    ProgressionScoreResult,
    VentricularMeasurements,
)
from numic.scoring.rules.models import NumicFlowRules, ProgressionRules


def _worsening(delta: float) -> float:
    return max(0.0, delta)


def _score_vi_ahw_progression(worsening_mm: float, rules: ProgressionRules) -> int:
    if worsening_mm < rules.vi_ahw_worsening_pt0_lt_mm:
        return 0
    if worsening_mm < rules.vi_ahw_worsening_pt1_lt_mm:
        return 1
    return 2


def _score_tod_progression(worsening_mm: float, rules: ProgressionRules) -> int:
    if worsening_mm < rules.tod_worsening_pt0_lt_mm:
        return 0
    if worsening_mm < rules.tod_worsening_pt1_lt_mm:
        return 1
    return 2


def _deltas(prior: VentricularMeasurements, current: VentricularMeasurements) -> ProgressionDeltas:
    return ProgressionDeltas(
        delta_vi_mm=_worsening(current.vi_mm - prior.vi_mm),
        delta_ahw_mm=_worsening(current.ahw_mm - prior.ahw_mm),
        delta_tod_mm=_worsening(current.tod_mm - prior.tod_mm),
    )


def compute_progression_score(
    prior: VentricularMeasurements,
    current: VentricularMeasurements,
    rules: NumicFlowRules,
) -> ProgressionScoreResult:
    p = rules.progression
    deltas = _deltas(prior, current)
    vi = _score_vi_ahw_progression(deltas.delta_vi_mm, p)
    ahw = _score_vi_ahw_progression(deltas.delta_ahw_mm, p)
    tod = _score_tod_progression(deltas.delta_tod_mm, p)
    return ProgressionScoreResult(
        vi_points=vi,
        ahw_points=ahw,
        tod_points=tod,
        progression_score=vi + ahw + tod,
        deltas_used=deltas,
    )
