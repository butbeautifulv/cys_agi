from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool

from cys_core.registry.tools import tool_registry


def require_sandbox(sandbox_id: str) -> None:
    if not sandbox_id or sandbox_id == "host":
        raise PermissionError("Tool requires sandbox context — denied on host")


class McpToolRegistry:
    """MCP-style tool registry — tools run only inside worker sandbox."""

    def resolve(self, tool_names: list[str], sandbox_id: str) -> list[BaseTool]:
        require_sandbox(sandbox_id)
        return tool_registry.resolve(tool_names)

    def invoke(self, tool_name: str, sandbox_id: str, args: dict[str, Any]) -> dict[str, Any]:
        require_sandbox(sandbox_id)
        base = tool_registry.get(tool_name)
        raw = base.invoke(args)
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
        return {"result": raw}


mcp_tool_registry = McpToolRegistry()
