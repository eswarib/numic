"""Concrete rule bundles and lookup."""

from __future__ import annotations

from numic.scoring.rules.models import (
    ClinicalRules,
    NumicFlowRules,
    ProgressionRules,
    RiskTierRules,
    StaticRules,
)

DEFAULT_SCORE_VERSION = "numic_flow_v1"

_STATIC_V1 = StaticRules(
    vi_percentile_moderate_min=97.0,
    vi_high_mm_above_reference=4.0,
    ahw_normal_max_mm=6.0,
    ahw_moderate_max_mm=10.0,
    tod_normal_max_mm=25.0,
    tod_high_min_mm=30.0,
)

# Example alternate policy: lower VI percentile gate (clinical governance required).
_STATIC_V2_PRE95 = StaticRules(
    vi_percentile_moderate_min=95.0,
    vi_high_mm_above_reference=4.0,
    ahw_normal_max_mm=6.0,
    ahw_moderate_max_mm=10.0,
    tod_normal_max_mm=25.0,
    tod_high_min_mm=30.0,
)

_PROGRESSION_V1 = ProgressionRules(
    vi_ahw_worsening_pt0_lt_mm=1.0,
    vi_ahw_worsening_pt1_lt_mm=2.0,
    tod_worsening_pt0_lt_mm=2.0,
    tod_worsening_pt1_lt_mm=4.0,
)

_CLINICAL_V1 = ClinicalRules(modifier_none=0, modifier_mild=1, modifier_clear=2)

_RISK_V1 = RiskTierRules(low_max=3, moderate_max=7)

NUMIC_FLOW_V1 = NumicFlowRules(
    score_version="numic_flow_v1",
    static=_STATIC_V1,
    progression=_PROGRESSION_V1,
    clinical=_CLINICAL_V1,
    risk_tier=_RISK_V1,
)

NUMIC_FLOW_V2_PRE95 = NumicFlowRules(
    score_version="numic_flow_v2_pre95",
    static=_STATIC_V2_PRE95,
    progression=_PROGRESSION_V1,
    clinical=_CLINICAL_V1,
    risk_tier=_RISK_V1,
)

_RULES: dict[str, NumicFlowRules] = {
    NUMIC_FLOW_V1.score_version: NUMIC_FLOW_V1,
    NUMIC_FLOW_V2_PRE95.score_version: NUMIC_FLOW_V2_PRE95,
}


def get_rules(score_version: str) -> NumicFlowRules:
    try:
        return _RULES[score_version]
    except KeyError as e:
        known = ", ".join(sorted(_RULES))
        raise ValueError(f"Unknown score_version={score_version!r}. Known: {known}") from e


def list_score_versions() -> tuple[str, ...]:
    return tuple(sorted(_RULES.keys()))
