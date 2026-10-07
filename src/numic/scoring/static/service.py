"""Static score (0–6) from VI, AHW, TOD using a versioned rule set (fixed or age-based thresholds)."""

from __future__ import annotations

from numic.api.schemas.scoring import MetricScore, StaticScoreResult, VentricularMeasurements
from numic.scoring.nomogram import get_table
from numic.scoring.rules.models import (
    FixedThreshold,
    MetricThreshold,
    NumicFlowRules,
    ReferenceLineThreshold,
)


class AgeRequiredError(ValueError):
    pass


def _points(value_mm: float, one_mm: float, two_mm: float, two_inclusive: bool) -> int:
    reaches_two = value_mm >= two_mm if two_inclusive else value_mm > two_mm
    if reaches_two:
        return 2
    if value_mm >= one_mm:
        return 1
    return 0


def score_metric(value_mm: float, threshold: MetricThreshold, age_weeks: float | None) -> MetricScore:
    """Score one metric. Reference-line thresholds raise ``OutOfChartRangeError`` outside the table."""
    if isinstance(threshold, FixedThreshold):
        one, two = threshold.one_point_min_mm, threshold.two_point_min_mm
        return MetricScore(
            value_mm=value_mm,
            points=_points(value_mm, one, two, threshold.two_point_inclusive),
            kind="fixed",
            one_point_mm=one,
            two_point_mm=two,
            two_point_inclusive=threshold.two_point_inclusive,
        )
    assert isinstance(threshold, ReferenceLineThreshold)
    if age_weeks is None:
        raise AgeRequiredError("age_at_scan_weeks is required for this rule set's age-based thresholds")
    line = get_table(threshold.table).line_at(age_weeks)
    one = line + threshold.one_point_offset_mm
    two = line + threshold.two_point_offset_mm
    return MetricScore(
        value_mm=value_mm,
        points=_points(value_mm, one, two, True),
        kind="reference_line",
        one_point_mm=round(one, 2),
        two_point_mm=round(two, 2),
        reference_table=threshold.table,
        reference_line_mm=round(line, 2),
        distance_from_line_mm=round(value_mm - line, 2),
    )


def compute_static_score(
    m: VentricularMeasurements,
    rules: NumicFlowRules,
    age_at_scan_weeks: float | None = None,
) -> StaticScoreResult:
    s = rules.static
    vi = score_metric(m.vi_mm, s.vi, age_at_scan_weeks)
    ahw = score_metric(m.ahw_mm, s.ahw, age_at_scan_weeks)
    tod = score_metric(m.tod_mm, s.tod, age_at_scan_weeks)
    return StaticScoreResult(
        vi_points=vi.points,
        ahw_points=ahw.points,
        tod_points=tod.points,
        static_score=vi.points + ahw.points + tod.points,
        age_at_scan_weeks=age_at_scan_weeks,
        vi=vi,
        ahw=ahw,
        tod=tod,
    )
