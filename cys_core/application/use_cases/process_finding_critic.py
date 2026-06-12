from __future__ import annotations

from collections.abc import Callable
from typing import Any, Awaitable, Protocol

from cys_core.application.ports.memory import InvestigationStateStore
from cys_core.domain.memory.services import MemoryWriteService
from cys_core.domain.security.guardrails import OutputGuardrails


class CriticStatusStore(Protocol):
    def record_finding(self, envelope: dict[str, Any]) -> None: ...
    def record_critic(self, feedback: dict[str, Any]) -> None: ...
    def record_awaiting_approval(self, record: dict[str, Any]) -> None: ...
    def record_escalation(self, record: dict[str, Any]) -> None: ...


class ProcessFindingCritic:
    """Validate finding envelope, optional L2 HITL, escalation, and episodic memory."""

    def __init__(
        self,
        *,
        guardrails: OutputGuardrails,
        store: CriticStatusStore,
        trust_score_threshold: float,
        publish_awaiting_approval: Callable[[dict[str, Any]], Awaitable[None]],
        publish_escalation_event: Callable[..., Awaitable[bool]],
        memory_writer: MemoryWriteService | None = None,
        investigation_store: InvestigationStateStore | None = None,
        record_memory_write: Callable[[str, str], None] | None = None,
        enqueue_revision: Callable[[dict[str, Any], str], Awaitable[None]] | None = None,
    ) -> None:
        self.guardrails = guardrails
        self.store = store
        self.trust_score_threshold = trust_score_threshold
        self.publish_awaiting_approval = publish_awaiting_approval
        self.publish_escalation_event = publish_escalation_event
        self.memory_writer = memory_writer
        self.investigation_store = investigation_store
        self.record_memory_write = record_memory_write
        self.enqueue_revision = enqueue_revision

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

    def _persist_approved_memory(self, envelope: dict[str, Any], payload: dict[str, Any], trust_score: float) -> None:
        if self.memory_writer is None:
            return
        tenant_id = str(payload.get("tenant_id", "default"))
        investigation_id = str(payload.get("correlation_id", payload.get("event_id", "")))
        if not investigation_id:
            return
        source_agent = str(envelope.get("sender", payload.get("agent", "unknown")))
        source_job_id = str(payload.get("job_id", ""))
        data = payload.get("data", payload)
        finding = data if isinstance(data, dict) else {"result": data}
        entry = self.memory_writer.append_finding(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            source_agent=source_agent,
            source_job_id=source_job_id,
            finding=finding,
            trust_score=trust_score,
        )
        if entry is not None and self.record_memory_write is not None:
            self.record_memory_write(tenant_id, entry.memory_type)
        if self.investigation_store is not None:
            self.investigation_store.append_finding(tenant_id, investigation_id, finding)

    async def execute(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = envelope.get("payload", {})
        trust_score = self._trust_score(payload)
        issues: list[str] = []
        if trust_score < self.trust_score_threshold:
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
            self.trust_score_threshold,
        )
        if issues and not feedback["approved"] and self.enqueue_revision is not None:
            feedback_text = "; ".join(issues)
            await self.enqueue_revision(envelope, feedback_text)
            feedback["revision_enqueued"] = True

        if needs_hitl:
            approval_record = {
                "event_id": payload.get("event_id"),
                "sender": envelope.get("sender"),
                "trust_score": trust_score,
                "issues_detected": issues,
                "envelope": envelope,
            }
            self.store.record_awaiting_approval(approval_record)
            await self.publish_awaiting_approval(approval_record)
            feedback["requires_hitl"] = True
        else:
            if feedback["approved"]:
                self._persist_approved_memory(envelope, payload, trust_score)
            if not needs_hitl and self._should_escalate(payload):
                severity = self._finding_severity(payload)
                escalated = await self.publish_escalation_event(
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
        envelope = approval_record.get("envelope", {})
        payload = envelope.get("payload", {})
        trust_score = self._trust_score(payload)
        self._persist_approved_memory(envelope, payload, trust_score)
        severity = self._finding_severity(payload)
        escalated = await self.publish_escalation_event(
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
