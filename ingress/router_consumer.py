from __future__ import annotations

import asyncio
import signal
from collections.abc import Awaitable, Callable
from typing import Any

from cys_core.domain.events.models import SecurityEvent
from cys_core.domain.events.router import EventRouter
from cys_core.infrastructure.kafka_events import consume_raw_event
from cys_core.registry.product_context import default_agents_root
from workers.orchestrator import WorkerOrchestrator

ConsumeRawFn = Callable[[float], Awaitable[SecurityEvent | None]]


class RouterConsumer:
    """Consume security.events.raw, route deterministically, enqueue worker jobs."""

    def __init__(
        self,
        router: EventRouter | None = None,
        orchestrator: WorkerOrchestrator | None = None,
        consume_raw: ConsumeRawFn | None = None,
    ) -> None:
        self.router = router or EventRouter.from_plans_dir(default_agents_root() / "plans")
        self.orchestrator = orchestrator or WorkerOrchestrator()
        self._consume_raw = consume_raw or consume_raw_event
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    async def process_one(self, timeout: float = 1.0) -> bool:
        event = await self._consume_raw(timeout)
        if event is None:
            return False
        decision = self.router.route(event)
        if decision.personas:
            await self.orchestrator.enqueue_from_routing(
                event.id,
                decision.personas,
                playbook_id=decision.playbook_id,
                payload=event.payload,
                correlation_id=event.correlation_id or event.id,
            )
        return True

    async def run(self, *, idle_timeout: float = 30.0) -> int:
        """Run until SIGTERM/SIGINT or idle_timeout seconds without messages."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.request_stop)

        processed = 0
        idle_elapsed = 0.0
        poll_interval = 1.0
        while not self._stop:
            handled = await self.process_one(timeout=poll_interval)
            if handled:
                processed += 1
                idle_elapsed = 0.0
                continue
            idle_elapsed += poll_interval
            if idle_timeout > 0 and idle_elapsed >= idle_timeout:
                break
        return processed


def run_router_consumer(*, idle_timeout: float = 0.0) -> int:
    return asyncio.run(RouterConsumer().run(idle_timeout=idle_timeout))
