from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_graph_workflow_build_cache_and_run(monkeypatch):
    import graph.workflow as workflow

    class FakeCompiledGraph:
        def __init__(self):
            self.invocations = []

        def invoke(self, payload, config):
            self.invocations.append((payload, config))
            return {"payload": payload, "config": config}

        async def ainvoke(self, payload, config):
            self.invocations.append((payload, config))
            return {"payload": payload, "config": config}

    class FakeStateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = []
            self.edges = []

        def add_node(self, name, func):
            self.nodes.append((name, func))

        def add_edge(self, source, dest):
            self.edges.append((source, dest))

        def add_conditional_edges(self, source, func):
            self.edges.append((source, func))

        def compile(self, checkpointer):
            self.checkpointer = checkpointer
            return FakeCompiledGraph()

    class FakeDag:
        def __init__(self):
            self.validated = False

        def validate_acyclic(self):
            self.validated = True

    fake_dag = FakeDag()
    monkeypatch.setattr(workflow, "_compiled_graph", None)
    monkeypatch.setattr(workflow, "_compiled_async_graph", None)
    monkeypatch.setattr(workflow, "StateGraph", FakeStateGraph)
    monkeypatch.setattr(workflow, "assessment_dag", lambda: fake_dag)

    class FakeWorkflowConnector:
        def open(self):
            return SimpleNamespace(checkpointer="default-cp")

        async def open_async(self):
            return SimpleNamespace(checkpointer="async-default-cp")

    monkeypatch.setattr(workflow, "get_persistence_connector", lambda: FakeWorkflowConnector())

    explicit = workflow.build_assessment_graph(SimpleNamespace(checkpointer="explicit-cp"))
    assert isinstance(explicit, FakeCompiledGraph)
    assert fake_dag.validated is True
    cached = workflow.build_assessment_graph()
    assert workflow.build_assessment_graph() is cached

    async_explicit = await workflow.build_assessment_graph_async(SimpleNamespace(checkpointer="async-explicit-cp"))
    assert isinstance(async_explicit, FakeCompiledGraph)
    async_cached = await workflow.build_assessment_graph_async()
    assert await workflow.build_assessment_graph_async() is async_cached

    async def fake_build_assessment_graph_async(persistence=None):
        return async_explicit

    monkeypatch.setattr(workflow, "build_assessment_graph_async", fake_build_assessment_graph_async)
    fresh = await workflow.run_assessment_async(
        "raw",
        thread_id="tid",
        scope={"authorized": False},
        persistence=SimpleNamespace(checkpointer="cp"),
    )
    assert fresh["payload"]["raw_input"] == "raw"
    assert fresh["payload"]["scope"] == {"authorized": False}
    assert fresh["config"]["configurable"]["thread_id"] == "tid"

    resumed = await workflow.run_assessment_async("", thread_id="tid", resume={"approved": True})
    assert resumed["payload"].resume == {"approved": True}

    def fake_asyncio_run(coro):
        coro.close()
        return {"sync": True}

    monkeypatch.setattr(workflow.asyncio, "run", fake_asyncio_run)
    assert workflow.run_assessment("raw") == {"sync": True}
