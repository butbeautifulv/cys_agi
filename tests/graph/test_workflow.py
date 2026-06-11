from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deprecated_workflow_routes_to_ingress(monkeypatch):
    import graph.workflow as workflow

    async def fake_aingest(event_type, payload, **kwargs):
        return (
            type("E", (), {"model_dump": lambda self: {"id": "e1", "type": event_type}})(),
            type("D", (), {"model_dump": lambda self: {"personas": ["soc"]}})(),
            ["job-1"],
        )

    import ingress.router as router_module

    monkeypatch.setattr(
        router_module,
        "get_event_ingress",
        lambda: SimpleNamespace(aingest=fake_aingest),
    )
    result = await workflow.run_assessment_async("raw input", thread_id="tid")
    assert result["deprecated"] is True
    assert result["job_ids"] == ["job-1"]
    assert result["event"]["type"] == "manual.investigation"


@pytest.mark.unit
def test_deprecated_run_assessment_sync(monkeypatch):
    import graph.workflow as workflow
    import ingress.router as router_module

    async def fake_aingest(event_type, payload, **kwargs):
        return (
            type("E", (), {"model_dump": lambda self: {"id": "e1"}})(),
            type("D", (), {"model_dump": lambda self: {}})(),
            [],
        )

    monkeypatch.setattr(
        router_module,
        "get_event_ingress",
        lambda: SimpleNamespace(aingest=fake_aingest),
    )
    sync = workflow.run_assessment("raw")
    assert sync["deprecated"] is True


@pytest.mark.unit
def test_deprecated_build_graph_returns_none():
    import graph.workflow as workflow

    assert workflow.build_assessment_graph() is None
