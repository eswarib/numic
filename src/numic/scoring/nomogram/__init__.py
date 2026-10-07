"""Age-based reference lines: age at scan and straight-line interpolation in published tables."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

TABLES_DIR = Path(__file__).resolve().parent.parent.parent / "rule_sets" / "tables"


class OutOfChartRangeError(ValueError):
    """Age at scan falls outside the reference table; the line is never extrapolated."""

    def __init__(self, table: ReferenceTable, age_weeks: float) -> None:
        self.table = table
        self.age_weeks = age_weeks
        super().__init__(
            f"Age at scan {format_ga(age_weeks)} wk is outside the {table.label} chart range "
            f"({format_ga(table.min_age_weeks)}–{format_ga(table.max_age_weeks)} wk)"
        )


class ScanBeforeBirthError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReferenceTable:
    name: str
    label: str
    unit: str
    verified: bool
    points: tuple[tuple[float, float], ...]
    """(age in weeks, line in mm), ascending by age."""

    @property
    def min_age_weeks(self) -> float:
        return self.points[0][0]

    @property
    def max_age_weeks(self) -> float:
        return self.points[-1][0]

    def line_at(self, age_weeks: float) -> float:
        """Reference line in mm at ``age_weeks``; raises ``OutOfChartRangeError`` outside the table."""
        if age_weeks < self.min_age_weeks or age_weeks > self.max_age_weeks:
            raise OutOfChartRangeError(self, age_weeks)
        for (a0, v0), (a1, v1) in zip(self.points, self.points[1:]):
            if a0 <= age_weeks <= a1:
                return v0 + (v1 - v0) * (age_weeks - a0) / (a1 - a0)
        return self.points[-1][1]


@lru_cache
def get_table(name: str) -> ReferenceTable:
    path = TABLES_DIR / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"Unknown reference table {name!r}")
    raw = json.loads(path.read_text())
    points = tuple((float(a), float(v)) for a, v in raw["points"])
    if any(b[0] <= a[0] for a, b in zip(points, points[1:])):
        raise ValueError(f"Reference table {name!r} ages must strictly increase")
    return ReferenceTable(
        name=raw["name"],
        label=raw["label"],
        unit=raw.get("unit", "mm"),
        verified=bool(raw.get("verified", False)),
        points=points,
    )


@dataclass(frozen=True, slots=True)
class AgeAtScan:
    day_of_life: int
    """Scan calendar day minus date of birth (birth day = day 0)."""
    age_weeks: float
    """Gestational age at birth + day of life / 7."""


def scan_day(measured_at: datetime, tz: str) -> date:
    """The scan's calendar day in the unit's local time (naive datetimes are taken as local)."""
    zone = ZoneInfo(tz)
    if measured_at.tzinfo is None:
        return measured_at.date()
    return measured_at.astimezone(zone).date()


def age_at_scan(
    date_of_birth: date,
    ga_weeks: int,
    ga_days: int,
    measured_at: datetime,
    tz: str = "Europe/London",
) -> AgeAtScan:
    day = (scan_day(measured_at, tz) - date_of_birth).days
    if day < 0:
        raise ScanBeforeBirthError("Scan date is before the date of birth")
    return AgeAtScan(day_of_life=day, age_weeks=ga_weeks + ga_days / 7 + day / 7)


def format_ga(age_weeks: float) -> str:
    """29.14 → '29+1' (completed weeks + days)."""
    total_days = int(round(age_weeks * 7, 6))
    return f"{total_days // 7}+{total_days % 7}"


__all__ = [
    "AgeAtScan",
    "OutOfChartRangeError",
    "ReferenceTable",
    "ScanBeforeBirthError",
    "age_at_scan",
    "format_ga",
    "get_table",
    "scan_day",
]
