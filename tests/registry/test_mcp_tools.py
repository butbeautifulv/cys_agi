from __future__ import annotations

import pytest

from cys_core.registry.mcp_tools import McpToolRegistry, require_sandbox


@pytest.mark.unit
def test_require_sandbox_denies_host():
    with pytest.raises(PermissionError):
        require_sandbox("host")
    with pytest.raises(PermissionError):
        require_sandbox("")


@pytest.mark.unit
def test_mcp_tool_invoke_in_sandbox():
    reg = McpToolRegistry()
    result = reg.invoke("dedup_alerts", "sandbox-1", {"alerts_text": "alert"})
    assert "deduplicated_count" in result
