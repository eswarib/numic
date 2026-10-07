"""Versioned threshold bundles for NumicFlow (no I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class FixedThreshold:
    """Fixed mm cut-offs: below ``one_point_min_mm`` → 0, then 1, then 2 from ``two_point_min_mm``."""

    one_point_min_mm: float
    """At or above this mm → at least 1 point."""

    two_point_min_mm: float
    """2 points at or above this mm (``two_point_inclusive``) or strictly above it."""

    two_point_inclusive: bool = True
    kind: Literal["fixed"] = "fixed"

    def __post_init__(self) -> None:
        if self.two_point_min_mm < self.one_point_min_mm:
            raise ValueError("two_point_min_mm must not be below one_point_min_mm")


@dataclass(frozen=True, slots=True)
class ReferenceLineThreshold:
    """Age-based line from a named table: 1 point at line + ``one_point_offset_mm``, 2 at line + ``two_point_offset_mm``."""

    table: str
    one_point_offset_mm: float
    two_point_offset_mm: float
    kind: Literal["reference_line"] = "reference_line"

    def __post_init__(self) -> None:
        if self.two_point_offset_mm <= self.one_point_offset_mm:
            raise ValueError("two_point_offset_mm must be greater than one_point_offset_mm")


MetricThreshold = FixedThreshold | ReferenceLineThreshold


@dataclass(frozen=True, slots=True)
class StaticRules:
    """Threshold for VI / AHW / TOD at a single timepoint; each is fixed or age-based."""

    vi: MetricThreshold
    ahw: MetricThreshold
    tod: MetricThreshold

    @property
    def needs_age(self) -> bool:
        return any(isinstance(t, ReferenceLineThreshold) for t in (self.vi, self.ahw, self.tod))


@dataclass(frozen=True, slots=True)
class ProgressionRules:
    """Worsening (mm) bands: points0 / 1 / 2 from two cutoffs per metric family."""

    vi_ahw_worsening_pt0_lt_mm: float
    vi_ahw_worsening_pt1_lt_mm: float
    tod_worsening_pt0_lt_mm: float
    tod_worsening_pt1_lt_mm: float


@dataclass(frozen=True, slots=True)
class ClinicalRules:
    """Modifier points for encoded concern level."""

    modifier_none: int
    modifier_mild: int
    modifier_clear: int


@dataclass(frozen=True, slots=True)
class RiskTierRules:
    """Maps total NumicFlow score (0–14) to three clinical bands.

    Only two numeric cutoffs are needed because the bands partition the line:

    - **Low:** ``total <= low_max`` (e.g. 0–3 when ``low_max=3``).
    - **Moderate:** ``low_max < total <= moderate_max`` (e.g. 4–7 when ``moderate_max=7``).
    - **High:** ``total > moderate_max`` (e.g. 8–14).

    There is no separate ``high_max`` because the score is bounded above by construction;
    “high” is everything above the moderate ceiling.
    """

    low_max: int
    """Inclusive upper bound of the low-risk band."""

    moderate_max: int
    """Inclusive upper bound of the moderate-risk band; any score above this is high."""

    def __post_init__(self) -> None:
        if self.moderate_max <= self.low_max:
            msg = f"moderate_max ({self.moderate_max}) must be greater than low_max ({self.low_max})"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class NumicFlowRules:
    """Full rule set for one published revision of a score_version family."""

    score_version: str
    """Rule-set family, e.g. ``numic_flow_levene``."""
    revision: int
    label: str
    source_citation: str
    static: StaticRules
    progression: ProgressionRules
    clinical: ClinicalRules
    risk_tier: RiskTierRules

    @property
    def revision_id(self) -> str:
        """Traceable ID stored with every result, e.g. ``numic_flow_levene@1``."""
        return f"{self.score_version}@{self.revision}"
