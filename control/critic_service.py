from __future__ import annotations

from typing import Any

from config import settings
from cys_core.domain.security.guardrails import OutputGuardrails
from cys_core.infrastructure.bus_transport import get_bus_transport
from cys_core.infrastructure.kafka_control_events import publish_awaiting_approval, publish_escalation_event
from control.status_store import get_status_store


class CriticService:
    """Async bus subscriber — validates findings, L2 HITL, and escalation."""

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

    def _finding_severity(self, payload: dict[str, Any]) -> str:
        data = payload.get("data", payload)
        if isinstance(data, dict):
            return str(data.get("severity", data.get("priority", "medium"))).lower()
        return "medium"

    def _should_escalate(self, payload: dict[str, Any]) -> bool:
        return self._finding_severity(payload) in ("critical", "high")

    async def handle_message(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = envelope.get("payload", {})
        trust_score = self._trust_score(payload)
        issues: list[str] = []
        if trust_score < settings.trust_score_threshold:
            issues.append("low_trust_score")
        data = payload.get("data", {})
        feedback = {
            "sender": envelope.get("sender"),
            "event_id": payload.get("event_id"),
            "trust_score": trust_score,
            "issues_detected": issues,
            "approved": not issues,
        }
        self.store.record_finding(envelope)
        self.store.record_critic(feedback)

        findings = [{"data": data if isinstance(data, dict) else payload}]
        needs_hitl = self.guardrails.requires_hitl(
            findings,
            trust_score,
            settings.trust_score_threshold,
        )
        if needs_hitl:
            approval_record = {
                "event_id": payload.get("event_id"),
                "sender": envelope.get("sender"),
                "trust_score": trust_score,
                "issues_detected": issues,
                "envelope": envelope,
            }
            self.store.record_awaiting_approval(approval_record)
            await publish_awaiting_approval(approval_record)
            feedback["requires_hitl"] = True
        elif not needs_hitl and self._should_escalate(payload):
            severity = self._finding_severity(payload)
            escalated = await publish_escalation_event(
                event_id=f"esc-{payload.get('event_id', 'unknown')}",
                source_persona=str(envelope.get("sender", "unknown")),
                payload={
                    "finding": data if isinstance(data, dict) else payload,
                    "event_id": payload.get("event_id"),
                    "original_sender": envelope.get("sender"),
                },
                severity="critical" if severity == "critical" else "high",
                correlation_id=str(payload.get("correlation_id", payload.get("event_id", ""))),
            )
            feedback["escalated"] = escalated
            if escalated:
                self.store.record_escalation(
                    {
                        "event_id": payload.get("event_id"),
                        "source_persona": envelope.get("sender"),
                        "severity": severity,
                    }
                )

        return feedback

    async def escalate_after_l2_approval(self, approval_record: dict[str, Any]) -> bool:
        """Publish escalation after human approves L2 awaiting_approval record."""
        envelope = approval_record.get("envelope", {})
        payload = envelope.get("payload", {})
        severity = self._finding_severity(payload)
        escalated = await publish_escalation_event(
            event_id=f"esc-{payload.get('event_id', 'unknown')}",
            source_persona=str(envelope.get("sender", approval_record.get("sender", "unknown"))),
            payload={
                "finding": payload.get("data", payload),
                "event_id": payload.get("event_id"),
                "l2_approved": True,
            },
            severity="critical" if severity == "critical" else "high",
            correlation_id=str(payload.get("correlation_id", payload.get("event_id", ""))),
        )
        if escalated:
            self.store.record_escalation(
                {
                    "event_id": payload.get("event_id"),
                    "source_persona": envelope.get("sender"),
                    "severity": severity,
                    "l2_approved": True,
                }
            )
        return escalated

    def register(self) -> None:
        self.transport.subscribe("critic", self.handle_message)


_critic_service: CriticService | None = None


def get_critic_service() -> CriticService:
    global _critic_service
    if _critic_service is None:
        _critic_service = CriticService()
        _critic_service.register()
    return _critic_service
