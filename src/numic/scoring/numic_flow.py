"""Full NumicFlow assessment: static + progression (if prior) + clinical → total and band."""

from __future__ import annotations

from numic.api.schemas.scoring import (
    ClinicalScoreInput,
    MetricScore,
    NumicFlowScoreResponse,
    RiskTier,
    VentricularMeasurements,
)
from numic.scoring.aggregate import numic_flow_total, risk_tier
from numic.scoring.clinical import compute_clinical_score
from numic.scoring.nomogram import format_ga, get_table
from numic.scoring.progression import compute_progression_score
from numic.scoring.rules.models import NumicFlowRules
from numic.scoring.static import compute_static_score


def score_numic_flow(
    current: VentricularMeasurements,
    rules: NumicFlowRules,
    *,
    age_at_scan_weeks: float | None = None,
    prior: VentricularMeasurements | None = None,
    clinical: ClinicalScoreInput | None = None,
) -> NumicFlowScoreResponse:
    """Raises ``ValueError`` subclasses (age missing, outside chart range) for the caller to map to 422."""
    static = compute_static_score(current, rules, age_at_scan_weeks)
    prog = compute_progression_score(prior, current, rules) if prior is not None else None
    clin = compute_clinical_score(clinical or ClinicalScoreInput(), rules)
    total = numic_flow_total(
        static.static_score, 0 if prog is None else prog.progression_score, clin.clinical_modifier
    )
    return NumicFlowScoreResponse(
        static=static,
        progression=prog,
        clinical=clin,
        numic_flow_score=total,
        risk_tier=risk_tier(total, rules),
        score_version=rules.score_version,
        rule_revision=rules.revision_id,
    )


def _pts(n: int) -> str:
    return f"{n} point" if n == 1 else f"{n} points"


def _mm(v: float) -> str:
    return f"{v:.1f} mm"


def _explain_metric(name: str, m: MetricScore, age_weeks: float | None) -> str:
    if m.kind == "reference_line":
        table = get_table(m.reference_table or "").label
        where = f"{table} line {_mm(m.reference_line_mm or 0)} at {format_ga(age_weeks or 0)} wk"
        d = m.distance_from_line_mm or 0
        if m.points == 2:
            pos = f"{_mm(d)} above the line, at or above line + {m.two_point_mm - (m.reference_line_mm or 0):.0f} mm"
        elif m.points == 1:
            pos = f"{_mm(d)} above the line" if d > 0 else "on the line"
        else:
            pos = f"{_mm(-d)} below the line"
        return f"{name} {_mm(m.value_mm)} is {pos} ({where}): {_pts(m.points)}."
    two = f"{'at or above' if m.two_point_inclusive else 'above'} {m.two_point_mm:g} mm"
    if m.points == 2:
        pos = two
    elif m.points == 1:
        pos = f"between {m.one_point_mm:g} and {m.two_point_mm:g} mm"
    else:
        pos = f"below {m.one_point_mm:g} mm"
    return f"{name} {_mm(m.value_mm)} is {pos}: {_pts(m.points)}."


def explain(
    result: NumicFlowScoreResponse,
    rules: NumicFlowRules,
    *,
    concern: str = "none",
    prior_label: str | None = None,
) -> list[str]:
    """Plain-language reasons for each layer and the band. Neutral wording: no clinical instructions."""
    s = result.static
    age = s.age_at_scan_weeks
    reasons = [
        _explain_metric("VI", s.vi, age),
        _explain_metric("AHW", s.ahw, age),
        _explain_metric("TOD", s.tod, age),
    ]
    p = result.progression
    if p is None:
        reasons.append("No earlier scan to compare with, so progression adds 0 points.")
    else:
        d = p.deltas_used
        since = f"Since {prior_label}" if prior_label else "Since the earlier scan"
        reasons.append(
            f"{since}: VI +{_mm(d.delta_vi_mm)} ({p.vi_points}), AHW +{_mm(d.delta_ahw_mm)} ({p.ahw_points}), "
            f"TOD +{_mm(d.delta_tod_mm)} ({p.tod_points}); progression {_pts(p.progression_score)}."
        )
    reasons.append(f"Clinical concern recorded as {concern}: {_pts(result.clinical.clinical_modifier)}.")
    lo, mid = rules.risk_tier.low_max, rules.risk_tier.moderate_max
    band_range = {
        RiskTier.low: f"0–{lo}",
        RiskTier.moderate: f"{lo + 1}–{mid}",
        RiskTier.high: f"{mid + 1}–14",
    }[result.risk_tier]
    reasons.append(
        f"Total {result.numic_flow_score} of 14 falls in the {result.risk_tier.value} band ({band_range})."
    )
    return reasons
