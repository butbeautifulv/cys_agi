from __future__ import annotations

from typing import Any

from cys_core.domain.security.guardrails import OutputGuardrails
from cys_core.infrastructure.bus_transport import get_bus_transport
from control.status_store import get_status_store


class CriticService:
    """Async bus subscriber — validates findings and emits feedback."""

    def __init__(self, guardrails: OutputGuardrails | None = None) -> None:
        self.guardrails = guardrails or OutputGuardrails()
        self.store = get_status_store()
        self.transport = get_bus_transport()

    def _trust_score(self, payload: dict[str, Any]) -> float:
        data = payload.get("data", payload)
        if isinstance(data, dict):
            conf = data.get("confidence")
            if conf is not None:
                return float(conf)
            priority = str(data.get("priority", data.get("severity", ""))).lower()
            if priority in ("critical", "high"):
                return 0.4
            if priority in ("medium",):
                return 0.7
        return 0.85

    async def handle_message(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = envelope.get("payload", {})
        trust_score = self._trust_score(payload)
        issues: list[str] = []
        if trust_score < 0.5:
            issues.append("low_trust_score")
        data = payload.get("data", {})
        if isinstance(data, dict):
            sev = str(data.get("severity", data.get("priority", ""))).lower()
            if sev in ("critical", "high"):
                issues.append("high_severity")
        feedback = {
            "sender": envelope.get("sender"),
            "event_id": payload.get("event_id"),
            "trust_score": trust_score,
            "issues_detected": issues,
            "approved": not issues,
        }
        self.store.record_finding(envelope)
        self.store.record_critic(feedback)
        return feedback

    def register(self) -> None:
        self.transport.subscribe("critic", self.handle_message)


_critic_service: CriticService | None = None


def get_critic_service() -> CriticService:
    global _critic_service
    if _critic_service is None:
        _critic_service = CriticService()
        _critic_service.register()
    return _critic_service
