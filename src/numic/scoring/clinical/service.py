"""Clinical modifier (0–2) from neonatal signs (versioned rules)."""

from __future__ import annotations

from numic.api.schemas.scoring import ClinicalConcern, ClinicalScoreInput, ClinicalScoreResult
from numic.scoring.rules.models import NumicFlowRules


def compute_clinical_score(clinical: ClinicalScoreInput, rules: NumicFlowRules) -> ClinicalScoreResult:
    c = rules.clinical
    mapping = {
        ClinicalConcern.none: c.modifier_none,
        ClinicalConcern.mild: c.modifier_mild,
        ClinicalConcern.clear: c.modifier_clear,
    }
    return ClinicalScoreResult(clinical_modifier=mapping[clinical.concern])
