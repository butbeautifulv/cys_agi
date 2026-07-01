from __future__ import annotations

import uuid
from typing import Any

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.application.runtime_config import get_max_spawn_depth
from cys_core.domain.runs.mode_policy import ModePolicy
from cys_core.domain.runs.models import InteractionMode, RunContext
from cys_core.domain.runs.plan_models import WorkPlan
from cys_core.domain.runs.spawn import MAX_SPAWN_DEPTH, SpawnWorkerPayload
from cys_core.domain.runs.state_models import RunState, RunStatus
from cys_core.domain.workers.models import WorkerJob


class SubagentSpawnBroker:
    """Validate and materialize spawn_worker requests into WorkerJobs."""

    def __init__(self, catalog: AgentCatalogPort, *, max_spawn_depth: int | None = None) -> None:
        self._catalog = catalog
        self._max_spawn_depth = max_spawn_depth if max_spawn_depth is not None else get_max_spawn_depth()

    def validate(self, payload: SpawnWorkerPayload, *, mode: InteractionMode | None) -> str | None:
        if not ModePolicy.allow_spawn(mode):
            return "spawn_not_allowed_in_mode"
        if payload.parent_context.spawn_depth >= self._max_spawn_depth or payload.parent_context.spawn_depth >= MAX_SPAWN_DEPTH:
            return "max_spawn_depth_exceeded"
        agent = self._catalog.get_agent(payload.persona)
        if agent is None or not agent.enabled:
            return "unknown_persona"
        return None

    def to_worker_job(self, payload: SpawnWorkerPayload, *, event_id: str = "") -> WorkerJob:
        child = payload.parent_context.spawn_child(f"job-{uuid.uuid4().hex[:12]}", persona=payload.persona)
        return WorkerJob(
            job_id=child.context_id,
            event_id=event_id or child.context_id,
            persona=payload.persona,
            payload={
                "sub_goal": payload.sub_goal,
                "persona_overlay": payload.persona_overlay,
                "spawn_depth": child.spawn_depth,
                "parent_correlation_key": payload.parent_context.correlation_key,
            },
            correlation_id=payload.parent_context.context_id,
            tenant_id=payload.parent_context.tenant_id,
        )
