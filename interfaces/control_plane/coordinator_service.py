from __future__ import annotations

from typing import Any

from bootstrap.container import get_container
from cys_core.application.use_cases.narrate_investigation import NarrateInvestigationProgress
from cys_core.infrastructure.bus_transport import get_bus_transport
from cys_core.infrastructure.memory.factory import get_memory_read_service
from cys_core.runtime.agent import get_runtime
from interfaces.control_plane.status_store import get_status_store


class CoordinatorService:
    """Control tower — narrates worker activity for the user."""

    def __init__(self) -> None:
        self.store = get_status_store()
        self.transport = get_bus_transport()
        container = get_container()
        self._narrator = NarrateInvestigationProgress(
            runtime=get_runtime(),
            investigation_store=container.get_investigation_state_store(),
            memory_reader=get_memory_read_service(),
        )

    async def handle_message(self, envelope: dict[str, Any]) -> None:
        sender = envelope.get("sender", "unknown")
        payload = envelope.get("payload", {})
        event_id = str(payload.get("event_id", "n/a"))
        tenant_id = str(payload.get("tenant_id", "default"))
        investigation_id = str(payload.get("correlation_id", payload.get("event_id", event_id)))
        narrative = await self._narrator.execute(
            sender=str(sender),
            event_id=event_id,
            tenant_id=tenant_id,
            investigation_id=investigation_id,
        )
        self.store.record_narrative(narrative)

    def register(self) -> None:
        self.transport.subscribe("coordinator", self.handle_message)


_coordinator_service: CoordinatorService | None = None


def get_coordinator_service() -> CoordinatorService:
    global _coordinator_service
    if _coordinator_service is None:
        _coordinator_service = CoordinatorService()
        _coordinator_service.register()
    return _coordinator_service
