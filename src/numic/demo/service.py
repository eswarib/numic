"""Score a baby's scans in date order: each scan is compared with the most recent earlier scan."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from numic.api.schemas.scoring import ClinicalConcern, ClinicalScoreInput, VentricularMeasurements
from numic.demo.db import as_utc
from numic.demo.models import DemoBaby, DemoScan
from numic.demo.schemas import (
    Assessment,
    BabyDetail,
    BabySummary,
    ReferenceLine,
    RuleSetInfo,
    ScanOut,
)
from numic.scoring.nomogram import ScanBeforeBirthError, age_at_scan, format_ga, get_table
from numic.scoring.numic_flow import explain, score_numic_flow
from numic.scoring.rules.models import FixedThreshold, NumicFlowRules


def rule_set_info(rules: NumicFlowRules) -> RuleSetInfo:
    lines = []
    for metric in ("vi", "ahw", "tod"):
        t = getattr(rules.static, metric)
        if isinstance(t, FixedThreshold):
            lines.append(
                ReferenceLine(
                    metric=metric,
                    kind="fixed",
                    label=f"{metric.upper()} cut-offs",
                    one_point_mm=t.one_point_min_mm,
                    two_point_mm=t.two_point_min_mm,
                )
            )
        else:
            table = get_table(t.table)
            lines.append(
                ReferenceLine(
                    metric=metric,
                    kind="reference_line",
                    label=table.label,
                    verified=table.verified,
                    one_point_offset_mm=t.one_point_offset_mm,
                    two_point_offset_mm=t.two_point_offset_mm,
                    points=list(table.points),
                )
            )
    return RuleSetInfo(
        score_version=rules.score_version,
        revision=rules.revision_id,
        label=rules.label,
        low_max=rules.risk_tier.low_max,
        moderate_max=rules.risk_tier.moderate_max,
        lines=lines,
    )


def _measurements(s: DemoScan) -> VentricularMeasurements:
    return VentricularMeasurements(vi_mm=max(s.vi_left_mm, s.vi_right_mm), ahw_mm=s.ahw_mm, tod_mm=s.tod_mm)


def _when(s: DemoScan, tz: str) -> str:
    local = as_utc(s.measured_at).astimezone(ZoneInfo(tz))
    return f"{local.day} {local:%b %H:%M}"


def score_scans(baby: DemoBaby, scans: list[DemoScan], rules: NumicFlowRules, tz: str) -> list[ScanOut]:
    ordered = sorted(scans, key=lambda s: as_utc(s.measured_at))
    out: list[ScanOut] = []
    for i, s in enumerate(ordered):
        prior = ordered[i - 1] if i else None
        m = _measurements(s)
        day = age_w = label = None
        try:
            age = age_at_scan(baby.date_of_birth, baby.ga_weeks, baby.ga_days, as_utc(s.measured_at), tz)
            day, age_w, label = age.day_of_life, age.age_weeks, format_ga(age.age_weeks)
            result = score_numic_flow(
                m,
                rules,
                age_at_scan_weeks=age.age_weeks,
                prior=None if prior is None else _measurements(prior),
                clinical=ClinicalScoreInput(concern=ClinicalConcern(s.clinical_concern)),
            )
            assessment = Assessment(
                status="scored",
                risk_tier=result.risk_tier,
                numic_flow_score=result.numic_flow_score,
                result=result,
                reasons=explain(
                    result,
                    rules,
                    concern=s.clinical_concern,
                    prior_label=None if prior is None else f"the scan on {_when(prior, tz)}",
                ),
                rule_revision=rules.revision_id,
                compared_with_scan_id=None if prior is None else prior.id,
            )
        except ScanBeforeBirthError as e:
            assessment = Assessment(status="not_scored", message=str(e), rule_revision=rules.revision_id)
        except ValueError as e:  # outside chart range: say so rather than guess
            assessment = Assessment(
                status="not_scored",
                message=f"Not scored: {e}. The line is not extended beyond the published chart.",
                rule_revision=rules.revision_id,
            )
        out.append(
            ScanOut(
                id=s.id,
                measured_at=as_utc(s.measured_at),
                day_of_life=day,
                age_weeks=None if age_w is None else round(age_w, 3),
                age_label=label,
                vi_left_mm=s.vi_left_mm,
                vi_right_mm=s.vi_right_mm,
                vi_mm=m.vi_mm,
                ahw_mm=s.ahw_mm,
                tod_mm=s.tod_mm,
                clinical_concern=ClinicalConcern(s.clinical_concern),
                read_only=s.sandbox_id is None,
                assessment=assessment,
            )
        )
    return out


def summarise(baby: DemoBaby, scored: list[ScanOut], story: str | None) -> BabySummary:
    latest = scored[-1] if scored else None
    a = latest.assessment if latest else None
    return BabySummary(
        id=baby.id,
        read_only=baby.sandbox_id is None,
        story=story,
        date_of_birth=baby.date_of_birth,
        ga_weeks=baby.ga_weeks,
        ga_days=baby.ga_days,
        ga_label=f"{baby.ga_weeks}+{baby.ga_days}",
        scan_count=len(scored),
        latest_scan_at=None if latest is None else latest.measured_at,
        latest_age_label=None if latest is None else latest.age_label,
        latest_status=None if a is None else a.status,
        latest_risk_tier=None if a is None else a.risk_tier,
        latest_score=None if a is None else a.numic_flow_score,
    )


def baby_detail(
    baby: DemoBaby,
    scans: list[DemoScan],
    rules: NumicFlowRules,
    tz: str,
    story: str | None,
    max_scans: int,
) -> BabyDetail:
    scored = score_scans(baby, scans, rules, tz)
    return BabyDetail(
        **summarise(baby, scored, story).model_dump(),
        scans=scored,
        can_add_scan=len(scored) < max_scans,
        rule_set=rule_set_info(rules),
    )
