"""Preterm cranial ultrasound timing protocol used for the seed babies."""

from numic.demo.protocol import protocol_scan_days


def _days(*args, **kw) -> list[tuple[int, str]]:
    return [(s.day, s.label) for s in protocol_scan_days(*args, **kw)]


def test_under_30_weeks_full_course() -> None:
    # born 26+0: weekly scans to 32+0 (day 42), 35 weeks day 63, term day 98, discharge day 103
    assert _days(26, 0, discharge_day=103) == [
        (0, "Admission"), (1, "Day 1"), (2, "Day 2"), (3, "Day 3"), (7, "Day 7"),
        (14, "Weekly"), (21, "Weekly"), (28, "Weekly"), (35, "Weekly"), (42, "Weekly"),
        (63, "35 weeks"), (98, "Term corrected"), (103, "Discharge"),
    ]


def test_weekly_runs_through_postmenstrual_week_32() -> None:
    days = _days(28, 3)
    assert (28, "Weekly") in days  # 32+3
    assert (35, "Weekly") not in days  # 33+3
    assert days[-2:] == [(46, "35 weeks"), (81, "Term corrected")]


def test_31_to_35_weeks_schedule() -> None:
    # admission, day 7, 35 weeks, term corrected; no day 1-3, weekly or discharge scans
    assert _days(33, 2, discharge_day=30) == [
        (0, "Admission"), (7, "Day 7"), (12, "35 weeks"), (47, "Term corrected"),
    ]


def test_35_week_scan_skipped_when_already_past() -> None:
    assert _days(34, 6) == [(0, "Admission"), (7, "Day 7"), (36, "Term corrected")]


def test_discharge_before_term_ends_the_schedule() -> None:
    days = _days(27, 0, discharge_day=60)
    assert days[-1] == (60, "Discharge")
    assert all(label != "Term corrected" for _, label in days)
