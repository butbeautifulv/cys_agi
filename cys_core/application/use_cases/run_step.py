from __future__ import annotations

import json
from typing import Any, Protocol

from cys_core.application.plans_as_hints import load_plan_hints
from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.application.ports.run_state import RunStateStorePort
from cys_core.application.ports.work_todo import WorkTodoStorePort
from cys_core.application.spawn_broker import SubagentSpawnBroker
from cys_core.domain.runs.checkpoint import checkpoint_key
from cys_core.domain.runs.models import InteractionMode, RunContext
from cys_core.domain.runs.plan_models import WorkPlan, WorkTodo
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


def _parse_work_plan(result: dict[str, Any]) -> WorkPlan | None:
    if "plan" in result and isinstance(result["plan"], dict):
        return WorkPlan.model_validate(result["plan"])
    for key in ("work_plan", "WorkPlan"):
        if key in result and isinstance(result[key], dict):
            return WorkPlan.model_validate(result[key])
    return None


def _status_from_result(result: dict[str, Any], *, mode: InteractionMode | None) -> RunStatus:
    if result.get("status") == "awaiting_user":
        return RunStatus.AWAITING_USER
    if mode == InteractionMode.PLAN:
        return RunStatus.AWAITING_PLAN_APPROVAL
    return RunStatus.IN_PROGRESS


class RunStep:
    """Execute one step for a RunContext (stateless or stateful)."""

    def __init__(
        self,
        *,
        runtime: RunRuntime,
        state_store: RunStateStorePort,
        catalog: AgentCatalogPort,
        todo_store: WorkTodoStorePort,
    ) -> None:
        self.runtime = runtime
        self.state_store = state_store
        self.catalog = catalog
        self.todo_store = todo_store
        self.spawn_broker = SubagentSpawnBroker(self.catalog)

    async def execute(
        self,
        ctx: RunContext,
        user_input: str,
        *,
        persona: str = "conductor",
    ) -> dict[str, Any]:
        state = self.state_store.get(ctx.tenant_id, ctx.context_id, ctx.kind.value)
        if state is None:
            state = RunState(run_context=ctx, goal=user_input, mode=ctx.mode, status=RunStatus.IN_PROGRESS)
        mode = ctx.mode or InteractionMode.AGENT
        session_id = checkpoint_key(ctx, persona=persona)
        prompt = json.dumps(
            {
                "goal": state.goal or user_input,
                "mode": mode.value,
                "input": user_input,
                "run_context": ctx.model_dump(),
                "routing_hints": load_plan_hints(),
                "todos": [t.model_dump() for t in self.todo_store.list_todos(ctx.tenant_id, ctx.context_id)],
            },
            ensure_ascii=False,
        )
        if mode == InteractionMode.PLAN:
            result = await self.runtime.arun(
                persona,
                prompt,
                session_id=session_id,
                tenant_id=ctx.tenant_id,
                investigation_id=ctx.context_id,
            )
            plan = _parse_work_plan(result if isinstance(result, dict) else {})
            if plan is None:
                plan = WorkPlan(rationale=str(result.get("rationale", "plan generated")), awaiting_user_input=False)
            state.plan = plan
            state.last_result = {"plan": plan.model_dump()}
            state.status = RunStatus.AWAITING_PLAN_APPROVAL
        elif ctx.is_stateful() or persona == "conductor":
            result = await self.runtime.arun(
                persona,
                prompt,
                session_id=session_id,
                tenant_id=ctx.tenant_id,
                investigation_id=ctx.context_id,
            )
            state.last_result = result if isinstance(result, dict) else {"raw": result}
            if isinstance(state.last_result, dict) and state.last_result.get("todos"):
                todos = [WorkTodo.model_validate(item) for item in state.last_result["todos"]]
                self.todo_store.replace_todos(ctx.tenant_id, ctx.context_id, todos)
                state.todos = todos
            state.status = _status_from_result(state.last_result, mode=mode)
        else:
            ephemeral_session = f"worker:{persona}:{ctx.context_id}"
            result = await self.runtime.arun(
                persona,
                prompt,
                session_id=ephemeral_session,
                tenant_id=ctx.tenant_id,
                investigation_id=ctx.context_id,
            )
            state.last_result = result if isinstance(result, dict) else {"raw": result}
            state.status = RunStatus.IN_PROGRESS
        self.state_store.upsert(state)
        return {"run_context": ctx.model_dump(), "result": state.last_result, "status": state.status.value}
