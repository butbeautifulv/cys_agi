from __future__ import annotations

from cys_core.domain.policy.defaults import ACTION_RISK_MAPPING
from cys_core.domain.policy.pure import classify_tool_risk_pure
from cys_core.domain.security.risk_level import RiskLevel

SEVERITY_RISK: dict[str, RiskLevel] = {
    "critical": RiskLevel.CRITICAL,
    "high": RiskLevel.HIGH,
    "medium": RiskLevel.MEDIUM,
    "low": RiskLevel.LOW,
    "info": RiskLevel.LOW,
    "informational": RiskLevel.LOW,
}


def classify_tool_risk(tool_name: str, profile_id: str | None = None) -> RiskLevel:
    if profile_id:
        try:
            from cys_core.infrastructure.catalog.profile_policy import get_profile_policy

            return classify_tool_risk_pure(tool_name, get_profile_policy(profile_id))
        except Exception:
            pass
    return classify_tool_risk_pure(tool_name, None)


def classify_severity(severity: str) -> RiskLevel:
    return SEVERITY_RISK.get(severity.lower().strip(), RiskLevel.MEDIUM)


def parse_threshold(value: str) -> RiskLevel:
    try:
        return RiskLevel(value.lower())
    except ValueError:
        return RiskLevel.LOW


__all__ = ["ACTION_RISK_MAPPING", "RiskLevel", "SEVERITY_RISK", "classify_tool_risk", "classify_severity", "parse_threshold"]
