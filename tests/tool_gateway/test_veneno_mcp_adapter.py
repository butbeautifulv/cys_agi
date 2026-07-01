from __future__ import annotations

import json

import httpx
import pytest

from cys_core.integrations.veneno_mcp_client import call_veneno_mcp_tool
from interfaces.gateways.tool.adapters.veneno_mcp import call_veneno_tool


@pytest.mark.unit
def test_call_veneno_mcp_disabled(monkeypatch):
    import cys_core.application.runtime_config as rc

    monkeypatch.setattr(rc, "_veneno_mcp_enabled", False)
    result = call_veneno_mcp_tool("run_active_scan", {"target": "10.0.0.1"})
    assert result["success"] is False
    assert "disabled" in result["error"]


@pytest.mark.unit
def test_call_veneno_mcp_success(monkeypatch):
    import cys_core.application.runtime_config as rc

    monkeypatch.setattr(rc, "_veneno_mcp_enabled", True)
    monkeypatch.setattr(rc, "_veneno_mcp_url", "http://veneno-mcp.test/mcp")

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["params"]["name"] == "run_active_scan"
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": json.dumps({"status": "queued"})}]},
            },
        )

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))

    class _ClientFactory:
        def __init__(self, timeout: float) -> None:
            self._client = mock_client

        def __enter__(self) -> httpx.Client:
            return self._client

        def __exit__(self, *args: object) -> None:
            self._client.close()

    monkeypatch.setattr("cys_core.integrations.veneno_mcp_client.httpx.Client", _ClientFactory)
    result = call_veneno_tool("run_active_scan", {"target": "10.0.0.1"})
    assert result["success"] is True
