from __future__ import annotations

from typing import Any

from cys_core.application.persona_quality_hooks import record_critic_verdict
from cys_core.infrastructure.catalog.profile_policy import get_trust_floor


class ProcessFindingCritic:
    """Lightweight finding critic — records persona quality signals."""

    def __init__(self, *, trust_threshold: float | None = None) -> None:
        self.trust_threshold = trust_threshold

    def execute(self, *, persona: str, finding: dict[str, Any], profile_id: str = "cybersec-soc") -> dict[str, Any]:
        threshold = self.trust_threshold
        if threshold is None:
            threshold = get_trust_floor(profile_id)
        trust_score = float(finding.get("trust_score", 0.75))
        passed = "error" not in finding and trust_score >= threshold
        record_critic_verdict(persona, passed=passed, trust_score=trust_score)
        return {"passed": passed, "trust_score": trust_score, "threshold": threshold}
