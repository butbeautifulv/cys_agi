from __future__ import annotations

import pytest

from cys_core.application.use_cases.run_step import RunStep
from cys_core.domain.runs.models import InteractionMode, RunContext
from cys_core.domain.runs.state_models import RunStatus
from cys_core.infrastructure.runs.memory import InMemoryRunStateStore
from cys_core.infrastructure.runs.todo_store import InMemoryWorkTodoStore


class _Catalog:
    def list_agents(self, **kwargs):
        return []

    def get_agent(self, name):
        return None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_step_plan_mode_awaits_approval():
    class FakeRuntime:
        async def arun(self, name, user_input, **kwargs):
            return {"plan": {"rationale": "step 1", "proposed_workers": ["soc"], "todos": []}}

    ctx = RunContext.from_session_id("sess-1", mode=InteractionMode.PLAN)
    store = InMemoryRunStateStore()
    step = RunStep(
        runtime=FakeRuntime(),
        state_store=store,
        catalog=_Catalog(),
        todo_store=InMemoryWorkTodoStore(),
    )
    out = await step.execute(ctx, "investigate host")
    assert out["status"] == RunStatus.AWAITING_PLAN_APPROVAL.value
    assert "plan" in out["result"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_step_stateless_job_uses_ephemeral_session():
    captured = {}

    class FakeRuntime:
        async def arun(self, name, user_input, **kwargs):
            captured.update(kwargs)
            return {"ok": True}

    ctx = RunContext.one_shot_job("job-1", mode=InteractionMode.AGENT)
    step = RunStep(
        runtime=FakeRuntime(),
        state_store=InMemoryRunStateStore(),
        catalog=_Catalog(),
        todo_store=InMemoryWorkTodoStore(),
    )
    await step.execute(ctx, "scan", persona="soc")
    assert captured["session_id"] == "worker:soc:job-1"
