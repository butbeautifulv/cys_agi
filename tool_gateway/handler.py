from __future__ import annotations

import json
from typing import Any

from cys_core.observability.metrics import metrics
from cys_core.registry.mcp_tools import require_sandbox
from cys_core.registry.tools import tool_registry
from tool_gateway.adapters import invoke_adapter
from tool_gateway.audit import record_tool_invocation
from tool_gateway.models import ToolInvokeRequest, ToolInvokeResponse
from tool_gateway.policy import ToolChainDepthExceeded, check_tool_chain
from tool_gateway.sanitize import sanitize_tool_output_or_raise


def _normalize_raw_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"raw": raw}
        return {"raw": raw}
    return {"result": raw}


def _execute_tool(request: ToolInvokeRequest) -> dict[str, Any]:
    adapter_result = invoke_adapter(request.tool_name, request.args)
    if adapter_result is not None:
        return adapter_result
    base = tool_registry.get(request.tool_name)
    raw = base.invoke(request.args)
    return _normalize_raw_result(raw)


def invoke_tool(request: ToolInvokeRequest) -> ToolInvokeResponse:
    """Authorize, execute tool backend, sanitize response, audit."""
    try:
        require_sandbox(request.sandbox_id)
        check_tool_chain(request)
        data = _execute_tool(request)
        sanitized = sanitize_tool_output_or_raise(data)
        response = ToolInvokeResponse(
            success=True,
            tool_name=request.tool_name,
            data=data,
            sanitized_payload=sanitized,
        )
    except ToolChainDepthExceeded as exc:
        response = ToolInvokeResponse(
            success=False,
            tool_name=request.tool_name,
            error=str(exc),
        )
    except Exception as exc:
        response = ToolInvokeResponse(
            success=False,
            tool_name=request.tool_name,
            error=str(exc),
        )
    record_tool_invocation(request, response)
    metrics.record_tool_invocation(request.tool_name, success=response.success)
    return response
