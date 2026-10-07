"""Age at scan and reference-line lookup."""

from datetime import date, datetime, timezone

import pytest

from numic.scoring.nomogram import (
    OutOfChartRangeError,
    ScanBeforeBirthError,
    age_at_scan,
    format_ga,
    get_table,
)


def test_interpolates_between_whole_weeks() -> None:
    t = get_table("levene_vi_p97")
    assert t.line_at(29.0) == pytest.approx(11.6)
    assert t.line_at(29.5) == pytest.approx(11.75)
    assert t.line_at(t.max_age_weeks) == pytest.approx(t.points[-1][1])


def test_outside_range_is_refused_not_extrapolated() -> None:
    t = get_table("levene_vi_p97")
    with pytest.raises(OutOfChartRangeError, match="outside"):
        t.line_at(t.min_age_weeks - 0.1)
    with pytest.raises(OutOfChartRangeError):
        t.line_at(t.max_age_weeks + 0.1)


def test_age_at_scan_worked_example() -> None:
    # born 2 Mar 2026 at 27+3; scan 14 Mar 09:00 → day 12, 29.14 wk (29+1)
    a = age_at_scan(date(2026, 3, 2), 27, 3, datetime(2026, 3, 14, 9, 0, tzinfo=timezone.utc))
    assert a.day_of_life == 12
    assert a.age_weeks == pytest.approx(27 + 3 / 7 + 12 / 7)
    assert format_ga(a.age_weeks) == "29+1"


def test_scan_on_day_of_birth_is_day_zero() -> None:
    a = age_at_scan(date(2026, 3, 2), 28, 0, datetime(2026, 3, 2, 23, 0))
    assert a.day_of_life == 0
    assert a.age_weeks == 28.0


def test_scan_before_birth_rejected() -> None:
    with pytest.raises(ScanBeforeBirthError):
        age_at_scan(date(2026, 3, 2), 28, 0, datetime(2026, 3, 1, 12, 0))


def test_scan_day_uses_unit_local_time() -> None:
    # 23:30 UTC on 1 Jul is 00:30 on 2 Jul in London (BST)
    scan = datetime(2026, 7, 1, 23, 30, tzinfo=timezone.utc)
    assert age_at_scan(date(2026, 7, 1), 30, 0, scan, "Europe/London").day_of_life == 1
    assert age_at_scan(date(2026, 7, 1), 30, 0, scan, "UTC").day_of_life == 0


def test_rule_set_file_matches_published_revision() -> None:
    """DEMO-N06: the demo uses the shared numic_flow_levene file at the published revision."""
    from numic.scoring.rules import get_rules

    r = get_rules("numic_flow_levene")
    assert r.revision_id == "numic_flow_levene@1"
    assert r.static.vi.table == "levene_vi_p97"
    assert r.static.vi.two_point_offset_mm == 4
