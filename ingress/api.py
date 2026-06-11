from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from control.status_store import get_status_store
from ingress.router import EventIngress, get_event_ingress


class EventIn(BaseModel):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: str = "medium"
    source: str = ""
    event_id: str | None = None
    correlation_id: str = ""


def create_app(ingress: EventIngress | None = None) -> FastAPI:
    """FastAPI app for event ingest and user status."""
    app = FastAPI(title="cys-agi event platform", version="0.2.0")
    event_ingress = ingress or get_event_ingress()
    store = get_status_store()

    @app.post("/events")
    async def post_event(event_in: EventIn) -> dict[str, Any]:
        from control.coordinator_service import get_coordinator_service
        from control.critic_service import get_critic_service

        get_critic_service()
        get_coordinator_service()
        event, decision, job_ids = await event_ingress.aingest(
            event_in.event_type,
            event_in.payload,
            severity=event_in.severity,
            source=event_in.source,
            event_id=event_in.event_id,
            correlation_id=event_in.correlation_id,
        )
        store.record_event(event.model_dump())
        return {
            "event": event.model_dump(),
            "routing": decision.model_dump(),
            "job_ids": job_ids,
        }

    @app.get("/status")
    async def get_status() -> dict[str, Any]:
        return store.snapshot()

    @app.post("/workers/process-one")
    async def process_one_worker() -> dict[str, Any]:
        from workers.orchestrator import WorkerOrchestrator

        result = await WorkerOrchestrator().process_next()
        if result is None:
            return {"status": "idle"}
        return {"status": "done", "result": result.model_dump()}

    return app
