from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_coordinator_creation_and_session(monkeypatch):
    import coordinator.deep_assessment as deep_assessment

    coordinator_def = SimpleNamespace(
        system_prompt="Coordinator prompt",
        interrupt_on={},
    )
    worker = SimpleNamespace(name="redteam")
    registry = SimpleNamespace(
        get=lambda name: coordinator_def,
        by_workers=lambda: [worker],
    )
    runtime = SimpleNamespace(to_deep_agent_subagent=lambda defn: {"name": defn.name})
    product_context = SimpleNamespace(skills_path="agents/skills")
    captured = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)

        async def fake_ainvoke(payload, config):
            return {"messages": [SimpleNamespace(content="async-done")], "config": config}

        return SimpleNamespace(
            invoke=lambda payload, config: {"messages": [SimpleNamespace(content="done")], "config": config},
            ainvoke=fake_ainvoke,
        )

    class FakeCoordinatorConnector:
        def open(self):
            return SimpleNamespace(checkpointer="cp", store="store")

        async def open_async(self):
            return SimpleNamespace(checkpointer="async-cp", store="async-store")

    monkeypatch.setattr(deep_assessment, "get_persistence_connector", lambda: FakeCoordinatorConnector())
    monkeypatch.setattr(deep_assessment, "get_agent_registry", lambda: registry)
    monkeypatch.setattr(deep_assessment, "get_runtime", lambda: runtime)
    monkeypatch.setattr(deep_assessment, "get_model_connector", lambda: SimpleNamespace(create_model=lambda: "model"))
    monkeypatch.setattr(deep_assessment, "get_product_context", lambda: product_context)
    monkeypatch.setattr(deep_assessment, "create_deep_agent", fake_create_deep_agent)

    agent = deep_assessment.create_assessment_coordinator()
    assert agent.invoke({"messages": []}, config={})["messages"][0].content == "done"
    assert captured["interrupt_on"]["run_active_scan"] is True
    assert captured["tools"] == []
    assert captured["subagents"] == [{"name": "redteam"}]

    result = deep_assessment.run_session("goal", thread_id="thread-a", persistence=SimpleNamespace(checkpointer="cp", store="s"))
    assert result["config"]["configurable"]["thread_id"] == "thread-a"
    async_result = await deep_assessment.run_session_async(
        "goal",
        thread_id="thread-b",
        persistence=SimpleNamespace(checkpointer="cp", store="s"),
    )
    assert async_result["messages"][0].content == "async-done"
