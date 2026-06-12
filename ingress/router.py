from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from config import settings
from cys_core.domain.events.models import RoutingDecision, SecurityEvent
from cys_core.observability.metrics import metrics
from cys_core.observability.tracing import bind_correlation_id, reset_correlation_id
from cys_core.domain.events.router import EventRouter
from cys_core.infrastructure.kafka_events import publish_raw_event_sync
from cys_core.registry.product_context import default_agents_root
from workers.orchestrator import WorkerOrchestrator


class EventIngress:
    """Accept structured events, route to workers, enqueue jobs."""

    def __init__(
        self,
        router: EventRouter | None = None,
        orchestrator: WorkerOrchestrator | None = None,
    ) -> None:
        self.router = router or EventRouter.from_plans_dir(default_agents_root() / "plans")
        self.orchestrator = orchestrator or WorkerOrchestrator()

    def ingest(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        severity: str = "medium",
        source: str = "",
        event_id: str | None = None,
        correlation_id: str = "",
    ) -> tuple[SecurityEvent, RoutingDecision, list[str]]:
        event = SecurityEvent(
            id=event_id or f"evt-{uuid.uuid4().hex[:12]}",
            type=event_type,  # type: ignore[arg-type]
            source=source,
            severity=severity,  # type: ignore[arg-type]
            payload=payload,
            correlation_id=correlation_id or "",
        )
        cid_token = bind_correlation_id(event.correlation_id or event.id)
        try:
            metrics.record_event_ingested(event.type)
            if settings.use_kafka and publish_raw_event_sync(event):
                decision = self.router.route(event)
                return event, decision, []

            decision = self.router.route(event)
            job_ids: list[str] = []
            if decision.personas:
                job_ids = self.orchestrator.enqueue_from_routing_sync(
                    event.id,
                    decision.personas,
                    playbook_id=decision.playbook_id,
                    payload=payload,
                    correlation_id=event.correlation_id or event.id,
                )
            return event, decision, job_ids
        finally:
            reset_correlation_id(cid_token)

    async def aingest(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        severity: str = "medium",
        source: str = "",
        event_id: str | None = None,
        correlation_id: str = "",
    ) -> tuple[SecurityEvent, RoutingDecision, list[str]]:
        event = SecurityEvent(
            id=event_id or f"evt-{uuid.uuid4().hex[:12]}",
            type=event_type,  # type: ignore[arg-type]
            source=source,
            severity=severity,  # type: ignore[arg-type]
            payload=payload,
            correlation_id=correlation_id or "",
        )
        cid_token = bind_correlation_id(event.correlation_id or event.id)
        try:
            metrics.record_event_ingested(event.type)
            if settings.use_kafka:
                from cys_core.infrastructure.kafka_events import publish_raw_event

                if await publish_raw_event(event):
                    decision = self.router.route(event)
                    return event, decision, []

            decision = self.router.route(event)
            job_ids: list[str] = []
            if decision.personas:
                job_ids = await self.orchestrator.enqueue_from_routing(
                    event.id,
                    decision.personas,
                    playbook_id=decision.playbook_id,
                    payload=payload,
                    correlation_id=event.correlation_id or event.id,
                )
            return event, decision, job_ids
        finally:
            reset_correlation_id(cid_token)


@lru_cache
def get_event_ingress() -> EventIngress:
    return EventIngress()
