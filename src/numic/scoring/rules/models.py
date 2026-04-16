"""Versioned threshold bundles for NumicFlow (no I/O)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StaticRules:
    """Thresholds for VI / AHW / TOD at a single timepoint."""

    vi_percentile_moderate_min: float
    """VI at or above this percentile enters the moderate/high pathway (e.g. 97 or 95)."""

    vi_high_mm_above_reference: float
    """High VI when vi_mm >= reference_mm + this delta (reference from overlay / nomogram)."""

    ahw_normal_max_mm: float
    """Strictly below this mm →0 AHW points."""

    ahw_moderate_max_mm: float
    """Up to this mm → 1 AHW point; above → 2."""

    tod_normal_max_mm: float
    """Strictly below this mm → 0 TOD points."""

    tod_high_min_mm: float
    """At or above this mm → 2 TOD points; between normal max and this → 1."""


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
    """Full rule set for one released score_version."""

    score_version: str
    static: StaticRules
    progression: ProgressionRules
    clinical: ClinicalRules
    risk_tier: RiskTierRules
