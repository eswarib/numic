"""Combine subscores and map to risk tier (versioned rules)."""

from __future__ import annotations

from numic.api.schemas.scoring import RiskTier
from numic.scoring.rules.models import NumicFlowRules


def numic_flow_total(static: int, progression: int, clinical: int) -> int:
    return static + progression + clinical


def risk_tier(total: int, rules: NumicFlowRules) -> RiskTier:
    r = rules.risk_tier
    if total <= r.low_max:
        return RiskTier.low
    if total <= r.moderate_max:
        return RiskTier.moderate
    return RiskTier.high
