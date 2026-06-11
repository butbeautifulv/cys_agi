from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from cys_core.domain.events.models import RoutingDecision, SecurityEvent
from cys_core.domain.events.router import EventRouter
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


@lru_cache
def get_event_ingress() -> EventIngress:
    return EventIngress()
