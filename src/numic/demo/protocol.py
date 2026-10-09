"""Cranial ultrasound timing protocol for preterm infants, used to schedule the seed babies' scans.

UCLH neonatal unit, section 10.1 (modified from Rennie, Hagmann & Robertson, *Neonatal Cerebral
Investigation*, CUP 2008, ch. 9); see ``docs/literature/Preterm-infants-cranial-ultrasound-timings.pptx``.

=================================================  ==========  ===========
Scan                                               < 30 weeks  31–35 weeks
=================================================  ==========  ===========
As soon as possible after admission (day 0)        yes         yes
Day 1, day 2, day 3                                yes
Day 7                                              yes         yes
Weekly to 32 weeks                                 yes
35 weeks                                           yes         yes
Term corrected (40 weeks)                          yes         yes
Discharge                                          yes
=================================================  ==========  ===========

Days are day of life (birth day = day 0); weeks are postmenstrual age (gestational age at birth +
day of life / 7), the same "age at scan" used for scoring.
"""

from __future__ import annotations

from dataclasses import dataclass

EARLY_PROTOCOL_MAX_GA_WEEKS = 30
"""Babies born before 30+0 weeks follow the intensive (< 30 weeks) column."""


@dataclass(frozen=True, slots=True)
class ScheduledScan:
    day: int
    label: str


def _day_at_pma(ga_total_days: int, pma_weeks: int) -> int:
    return pma_weeks * 7 - ga_total_days


def protocol_scan_days(ga_weeks: int, ga_days: int, discharge_day: int | None = None) -> list[ScheduledScan]:
    """Every scan the protocol asks for, in order: to discharge for < 30 weeks, to term for 31–35 weeks."""
    ga = ga_weeks * 7 + ga_days
    early = ga_weeks < EARLY_PROTOCOL_MAX_GA_WEEKS
    plan: dict[int, str] = {0: "Admission"}
    if early:
        plan.update({1: "Day 1", 2: "Day 2", 3: "Day 3"})
    plan.setdefault(7, "Day 7")
    if early:
        day = 14
        while (ga + day) // 7 <= 32:  # weekly while in postmenstrual week 32 or earlier
            plan.setdefault(day, "Weekly")
            day += 7
    for pma, label in ((35, "35 weeks"), (40, "Term corrected")):
        d = _day_at_pma(ga, pma)
        if d > max(plan):
            plan[d] = label
    if early and discharge_day is not None:
        plan = {d: label for d, label in plan.items() if d < discharge_day}
        plan[discharge_day] = "Discharge"
    return [ScheduledScan(d, plan[d]) for d in sorted(plan)]
