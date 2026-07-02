from __future__ import annotations

import pytest
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest

from cys_core.application.reasoning.sgr_policy import ResolvedSgrPolicy
from cys_core.middleware.sgr_reasoning_middleware import SchemaGuidedReasoningMiddleware
from cys_core.middleware.sgr_session import SgrSessionState


@pytest.mark.unit
def test_sgr_gate_blocks_action_without_reasoning():
    session = SgrSessionState()
    mw = SchemaGuidedReasoningMiddleware(
        policy=ResolvedSgrPolicy(enabled=True, mode="sgr_hybrid", require_before_action=True),
        session=session,
    )
    request = ToolCallRequest(
        tool_call={"name": "query_siem_readonly", "id": "1", "args": {}},
        tool=None,  # type: ignore[arg-type]
        state={},
        runtime=None,  # type: ignore[arg-type]
    )

    def handler(_req):
        return ToolMessage(content="ok", tool_call_id="1")

    result = mw.wrap_tool_call(request, handler)
    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert "reasoning_step" in result.content


@pytest.mark.unit
def test_sgr_gate_allows_action_after_reasoning():
    session = SgrSessionState()
    from cys_core.domain.reasoning.sgr_models import SchemaGuidedReasoningStep

    session.mark_reasoning(
        SchemaGuidedReasoningStep(
            reasoning_steps=["a", "b"],
            current_situation="x",
            plan_status="y",
            task_completed=False,
        )
    )
    mw = SchemaGuidedReasoningMiddleware(
        policy=ResolvedSgrPolicy(enabled=True, mode="sgr_hybrid", require_before_action=True),
        session=session,
    )
    request = ToolCallRequest(
        tool_call={"name": "query_siem_readonly", "id": "1", "args": {}},
        tool=None,  # type: ignore[arg-type]
        state={},
        runtime=None,  # type: ignore[arg-type]
    )

    def handler(_req):
        return ToolMessage(content="ok", tool_call_id="1")

    result = mw.wrap_tool_call(request, handler)
    assert isinstance(result, ToolMessage)
    assert result.content == "ok"
