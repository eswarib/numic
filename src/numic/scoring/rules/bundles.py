"""Rule-set lookup. Thresholds come from ``rule_sets/*.json``; this module never holds clinical constants."""

from __future__ import annotations

from functools import lru_cache

from numic.core.config import DEFAULT_SCORE_VERSION, get_settings
from numic.scoring.rules.loader import load_rule_set_files
from numic.scoring.rules.models import NumicFlowRules

__all__ = ["DEFAULT_SCORE_VERSION", "get_rules", "list_rule_sets", "list_score_versions"]


@lru_cache
def _all_rules() -> dict[str, NumicFlowRules]:
    return load_rule_set_files()


def _enabled() -> dict[str, NumicFlowRules]:
    enabled = set(get_settings().enabled_score_versions)
    return {k: v for k, v in _all_rules().items() if k in enabled}


def get_rules(score_version: str | None = None) -> NumicFlowRules:
    """Look up an enabled rule set by family (``numic_flow_levene``) or revision (``numic_flow_levene@1``)."""
    requested = score_version or get_settings().default_score_version
    family, _, revision = requested.partition("@")
    rules = _enabled().get(family)
    if rules is None or (revision and revision != str(rules.revision)):
        known = ", ".join(sorted(r.revision_id for r in _enabled().values()))
        raise ValueError(f"Unknown or retired score_version={requested!r}. Known: {known}")
    return rules


def list_score_versions() -> tuple[str, ...]:
    return tuple(sorted(_enabled()))


def list_rule_sets() -> tuple[NumicFlowRules, ...]:
    return tuple(_enabled()[k] for k in list_score_versions())
