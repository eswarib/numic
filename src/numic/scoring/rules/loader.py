"""Load rule sets from their JSON files (factory values for revision 1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from numic.scoring.nomogram import get_table
from numic.scoring.rules.models import (
    ClinicalRules,
    FixedThreshold,
    MetricThreshold,
    NumicFlowRules,
    ProgressionRules,
    ReferenceLineThreshold,
    RiskTierRules,
    StaticRules,
)

RULE_SETS_DIR = Path(__file__).resolve().parent.parent.parent / "rule_sets"


def _metric(raw: dict[str, Any]) -> MetricThreshold:
    kind = raw["kind"]
    if kind == "fixed":
        return FixedThreshold(
            one_point_min_mm=float(raw["one_point_min_mm"]),
            two_point_min_mm=float(raw["two_point_min_mm"]),
            two_point_inclusive=bool(raw.get("two_point_inclusive", True)),
        )
    if kind == "reference_line":
        get_table(raw["table"])  # fail at load time if the table is missing
        return ReferenceLineThreshold(
            table=raw["table"],
            one_point_offset_mm=float(raw["one_point_offset_mm"]),
            two_point_offset_mm=float(raw["two_point_offset_mm"]),
        )
    raise ValueError(f"Unknown threshold kind {kind!r}")


def rules_from_dict(raw: dict[str, Any]) -> NumicFlowRules:
    s, p, c, r = raw["static"], raw["progression"], raw["clinical"], raw["risk_tier"]
    vi_ahw, tod = p["vi_ahw_worsening_mm"], p["tod_worsening_mm"]
    return NumicFlowRules(
        score_version=raw["score_version"],
        revision=int(raw["revision"]),
        label=raw["label"],
        source_citation=raw.get("source_citation", ""),
        static=StaticRules(vi=_metric(s["vi"]), ahw=_metric(s["ahw"]), tod=_metric(s["tod"])),
        progression=ProgressionRules(
            vi_ahw_worsening_pt0_lt_mm=float(vi_ahw[0]),
            vi_ahw_worsening_pt1_lt_mm=float(vi_ahw[1]),
            tod_worsening_pt0_lt_mm=float(tod[0]),
            tod_worsening_pt1_lt_mm=float(tod[1]),
        ),
        clinical=ClinicalRules(
            modifier_none=int(c["none"]),
            modifier_mild=int(c["mild"]),
            modifier_clear=int(c["clear"]),
        ),
        risk_tier=RiskTierRules(low_max=int(r["low_max"]), moderate_max=int(r["moderate_max"])),
    )


def load_rule_set_files(directory: Path = RULE_SETS_DIR) -> dict[str, NumicFlowRules]:
    """Active rule sets keyed by family name; retired files are skipped."""
    out: dict[str, NumicFlowRules] = {}
    for path in sorted(directory.glob("*.json")):
        raw = json.loads(path.read_text())
        if raw.get("status", "active") != "active":
            continue
        rules = rules_from_dict(raw)
        out[rules.score_version] = rules
    return out
