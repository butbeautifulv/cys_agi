from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel


class DemoSchema(BaseModel):
    value: str


@pytest.mark.unit
@pytest.mark.asyncio
async def test_graph_nodes_success_error_and_hitl_paths(monkeypatch):
    import graph.nodes as nodes

    class FakeNodeRateLimiter:
        async def acheck(self, _key):
            return None

    monkeypatch.setattr(nodes, "_rate_limiter", FakeNodeRateLimiter())
    monkeypatch.setattr(
        nodes,
        "_sanitizer",
        SimpleNamespace(sanitize=lambda text, **kwargs: f"safe:{text}"),
    )

    ingest = await nodes.ingest_node({"raw_input": "raw", "session_id": "sid", "scope": {"authorized": False}})
    assert ingest["sanitized_input"] == "safe:raw"
    assert ingest["scope"] == {"authorized": False}

    defs = [SimpleNamespace(name="redteam"), SimpleNamespace(name="network")]
    monkeypatch.setattr(nodes, "_registry", SimpleNamespace(by_role=lambda role: defs))
    sends = nodes.dispatch_node({"sanitized_input": "safe", "session_id": "sid"})
    assert [send.arg["agent_name"] for send in sends] == ["redteam", "network"]

    class FakeRuntime:
        def __init__(self):
            self.result = {"severity": "low"}
            self.error: Exception | None = None

        async def arun(self, *_args, **_kwargs):
            if self.error:
                raise self.error
            return self.result

    runtime = FakeRuntime()
    bus = SimpleNamespace(send_message=MagicMock(return_value={"signed": True}), receive_message=MagicMock(), record_agent_failure=MagicMock())
    monkeypatch.setattr(nodes, "_runtime", runtime)
    monkeypatch.setattr(nodes, "_bus", bus)
    success = await nodes.run_agent_node({"agent_name": "redteam", "sanitized_input": "safe", "session_id": "sid"})
    assert success["findings"][0]["data"] == {"severity": "low"}
    bus.receive_message.assert_called_once()

    runtime.error = RuntimeError("agent failed")
    failure = await nodes.run_agent_node({"agent_name": "redteam", "sanitized_input": "safe", "session_id": "sid"})
    assert failure["errors"] == ["redteam: agent failed"]
    bus.record_agent_failure.assert_called_with("redteam")

    runtime.error = None
    runtime.result = {"trust_score": 0.8}
    monkeypatch.setattr(nodes.schema_registry, "get", lambda name: DemoSchema if name == "CriticResult" else None)
    monkeypatch.setattr(nodes, "_guardrails", SimpleNamespace(validate_schema=lambda data, schema: DemoSchema(value="critic")))
    critic = await nodes.critic_node({"findings": [{"a": 1}], "session_id": "sid"})
    assert critic["critic_result"] == {"value": "critic"}

    monkeypatch.setattr(nodes.schema_registry, "get", lambda name: None)
    assert (await nodes.critic_node({"findings": [], "session_id": "sid"}))["critic_result"] == {"trust_score": 0.8}

    runtime.error = RuntimeError("critic failed")
    error = await nodes.critic_node({"findings": [], "session_id": "sid"})
    assert error["critic_result"]["trust_score"] == 0.0
    assert error["errors"] == ["critic: critic failed"]

    monkeypatch.setattr(
        nodes,
        "_hitl_policy",
        nodes.HitlPolicy(SimpleNamespace(requires_hitl=lambda findings, score, threshold: False)),
    )
    assert nodes.hitl_gate_node({"critic_result": {"trust_score": 1}, "findings": []}) == {
        "approved": True,
        "pending_approval": None,
    }

    monkeypatch.setattr(
        nodes,
        "_hitl_policy",
        nodes.HitlPolicy(SimpleNamespace(requires_hitl=lambda findings, score, threshold: True)),
    )
    monkeypatch.setattr(nodes.settings, "stage", "dev")
    monkeypatch.setattr(nodes.settings, "hitl_auto_approve_threshold", "medium")
    auto = nodes.hitl_gate_node({"critic_result": {"trust_score": 0.1}, "findings": []})
    assert auto["pending_approval"]["auto_approved"] is True

    monkeypatch.setattr(nodes.settings, "stage", "test")
    monkeypatch.setattr(nodes, "interrupt", lambda preview: {"approved": False})
    manual = nodes.hitl_gate_node(
        {
            "critic_result": {"trust_score": 0.1},
            "findings": [{"data": {"severity": "critical"}}, {"data": {"severity": "low"}}],
        }
    )
    assert manual["approved"] is False
    assert len(manual["pending_approval"]["high_severity"]) == 1

    monkeypatch.setattr(nodes, "interrupt", lambda preview: True)
    assert nodes.hitl_gate_node({"critic_result": {"trust_score": 0.1}, "findings": []})["approved"] is True

    rejected = nodes.report_node({"approved": False, "pending_approval": {"reason": "manual"}})
    assert rejected["report"]["status"] == "rejected"
    published = nodes.report_node(
        {"approved": True, "session_id": "sid", "findings": [], "critic_result": {}, "errors": ["warn"]}
    )
    assert published["report"]["status"] == "published"
