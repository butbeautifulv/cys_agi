from __future__ import annotations

import uuid
from typing import Any

from bootstrap.container import get_container
from bootstrap.settings import settings
from cys_core.application.use_cases.process_finding_critic import ProcessFindingCritic
from cys_core.domain.security.guardrails import OutputGuardrails
from cys_core.domain.workers.models import WorkerJob
from cys_core.infrastructure.bus_transport import get_bus_transport
from cys_core.infrastructure.kafka_control_events import (
    publish_awaiting_approval,
    publish_escalation_event,
)
from cys_core.infrastructure.memory.factory import get_memory_write_service
from cys_core.observability.metrics import metrics
from interfaces.control_plane.status_store import get_status_store
from interfaces.worker.orchestrator import WorkerOrchestrator


class CriticService:
    """Async bus subscriber — validates findings, L2 HITL, escalation, and memory."""

    def __init__(self, guardrails: OutputGuardrails | None = None) -> None:
        self.guardrails = guardrails or OutputGuardrails()
        self.store = get_status_store()
        self.transport = get_bus_transport()

    async def _enqueue_revision(self, envelope: dict[str, Any], feedback: str) -> None:
        payload = envelope.get("payload", {})
        persona = str(envelope.get("sender", payload.get("agent", "soc")))
        orchestrator = WorkerOrchestrator(persona=persona)
        job = WorkerJob(
            job_id=f"{persona}-revision-{uuid.uuid4().hex[:8]}",
            event_id=str(payload.get("event_id", "")),
            persona=persona,
            correlation_id=str(payload.get("correlation_id", payload.get("event_id", ""))),
            tenant_id=str(payload.get("tenant_id", "default")),
            feedback=feedback,
            payload=dict(payload),
        )
        await orchestrator.queue.aenqueue(job.model_dump())

    def _processor(self) -> ProcessFindingCritic:
        container = get_container()
        judge = container.get_judge_backend() if settings.critic_use_llm_judge else None
        return ProcessFindingCritic(
            guardrails=self.guardrails,
            store=self.store,
            trust_score_threshold=settings.trust_score_threshold,
            publish_awaiting_approval=publish_awaiting_approval,
            publish_escalation_event=publish_escalation_event,
            memory_writer=get_memory_write_service(),
            investigation_store=container.get_investigation_state_store(),
            record_memory_write=metrics.record_memory_write,
            enqueue_revision=self._enqueue_revision,
            judge_backend=judge,
        )

    async def handle_message(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return await self._processor().execute(envelope)

    async def escalate_after_l2_approval(self, approval_record: dict[str, Any]) -> bool:
        return await self._processor().escalate_after_l2_approval(approval_record)

    def register(self) -> None:
        self.transport.subscribe("critic", self.handle_message)


_critic_service: CriticService | None = None


def get_critic_service() -> CriticService:
    global _critic_service
    if _critic_service is None:
        _critic_service = CriticService()
        _critic_service.register()
    return _critic_service
