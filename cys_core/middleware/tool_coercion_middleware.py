from __future__ import annotations

from collections.abc import Callable
from typing import Any, Awaitable

from langchain.agents.middleware.types import AgentMiddleware
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from cys_core.application.runs.tool_coercion import coerce_tool_args


class ToolCoercionMiddleware(AgentMiddleware):
    """Coerce tool call arguments before handler execution."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> Any:
        raw_args = request.tool_call.get("args", {})
        if isinstance(raw_args, dict):
            request.tool_call["args"] = coerce_tool_args(raw_args)
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[Any] | Any],
    ) -> Any:
        raw_args = request.tool_call.get("args", {})
        if isinstance(raw_args, dict):
            request.tool_call["args"] = coerce_tool_args(raw_args)
        result = handler(request)
        if hasattr(result, "__await__"):
            return await result
        return result
