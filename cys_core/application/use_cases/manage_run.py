from __future__ import annotations

from typing import Any, Protocol

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.application.ports.run_state import RunStateStorePort
from cys_core.application.ports.work_todo import WorkTodoStorePort
from cys_core.application.spawn_broker import SubagentSpawnBroker
from cys_core.application.use_cases.run_step import RunStep
from cys_core.domain.runs.models import ContextKind, InteractionMode, RunContext
from cys_core.domain.runs.plan_models import PlanApproval
from cys_core.domain.runs.state_models import RunState, RunStatus


class RunRuntime(Protocol):
    async def arun(
        self,
        name: str,
        user_input: str,
        *,
        session_id: str | None = None,
        tenant_id: str = "default",
        investigation_id: str = "",
    ) -> dict[str, Any]: ...


class ManageRun:
    """Resolve run context from store and delegate steps to RunStep."""

    def __init__(
        self,
        *,
        runtime: RunRuntime,
        state_store: RunStateStorePort,
        catalog: AgentCatalogPort,
        todo_store: WorkTodoStorePort,
    ) -> None:
        self._step = RunStep(
            runtime=runtime,
            state_store=state_store,
            catalog=catalog,
            todo_store=todo_store,
        )
        self._state_store = state_store

    def get_context(self, run_id: str, tenant_id: str = "default") -> RunContext:
        for kind in (ContextKind.SESSION, ContextKind.JOB, ContextKind.INVESTIGATION):
            state = self._state_store.get(tenant_id, run_id, kind.value)
            if state is not None:
                return state.run_context
        raise KeyError(f"Run not found: {run_id}")

    def save_context(self, ctx: RunContext, *, goal: str = "") -> None:
        state = self._state_store.get(ctx.tenant_id, ctx.context_id, ctx.kind.value)
        if state is None:
            state = RunState(run_context=ctx, goal=goal, mode=ctx.mode, status=RunStatus.IN_PROGRESS)
        else:
            state = state.model_copy(update={"run_context": ctx})
        self._state_store.upsert(state)

    async def create_and_step(
        self,
        ctx: RunContext,
        user_input: str,
        *,
        persona: str = "conductor",
    ) -> dict[str, Any]:
        self.save_context(ctx, goal=user_input)
        return await self._step.execute(ctx, user_input, persona=persona)

    async def step(
        self,
        run_id: str,
        message: str,
        *,
        tenant_id: str = "default",
        mode: InteractionMode | None = None,
        persona: str = "conductor",
    ) -> dict[str, Any]:
        ctx = self.get_context(run_id, tenant_id)
        if mode is not None:
            ctx = ctx.model_copy(update={"mode": mode})
            self.save_context(ctx)
        return await self._step.execute(ctx, message, persona=persona)

    async def approve_plan(
        self,
        run_id: str,
        approval: PlanApproval,
        *,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        ctx = self.get_context(run_id, tenant_id)
        if approval.decision == "reject":
            state = RunState(run_context=ctx, status=RunStatus.CLOSED)
            self._state_store.upsert(state)
            return {"run_context": ctx.model_dump(), "result": {"status": "rejected"}}
        ctx = ctx.model_copy(update={"mode": InteractionMode.AGENT})
        self.save_context(ctx)
        return await self._step.execute(ctx, "execute approved plan")
