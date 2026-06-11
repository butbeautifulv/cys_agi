from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import ToolMessage


def request(name: str, *, args: dict | None = None, call_id: str = "call-1"):
    return SimpleNamespace(tool_call={"name": name, "args": args or {}, "id": call_id})


@pytest.mark.unit
def test_security_middleware_paths_and_hitl_builder(monkeypatch):
    import cys_core.middleware.security_middleware as security_middleware

    middleware = security_middleware.SecurityMiddleware("agent-a", "session-a")
    middleware.rate_limiter = SimpleNamespace(check=MagicMock())
    middleware.monitor = SimpleNamespace(log_security_event=MagicMock(), log_tool_call=MagicMock())
    monkeypatch.setattr(security_middleware.settings, "stage", "test")

    class HighRisk:
        value = "high"

        def __gt__(self, _other):
            return True

    monkeypatch.setattr(security_middleware, "classify_tool_risk", lambda _name: HighRisk())
    gated = middleware.wrap_tool_call(request("danger"), lambda req: ToolMessage(content="ok", tool_call_id="x"))
    assert gated.status == "error"
    assert "requires human approval" in gated.content

    middleware.rate_limiter.check.side_effect = RuntimeError("too many")
    limited = middleware.wrap_tool_call(request("parse_netflow"), lambda req: ToolMessage(content="ok", tool_call_id="x"))
    assert limited.status == "error"
    middleware.monitor.log_security_event.assert_called()

    middleware.rate_limiter.check.side_effect = None
    monkeypatch.setattr(security_middleware, "classify_tool_risk", lambda _name: security_middleware.RiskLevel.LOW)
    handled = middleware.wrap_tool_call(
        request("parse_netflow"),
        lambda req: ToolMessage(content="ok", tool_call_id=req.tool_call["id"]),
    )
    assert handled.content == "ok"
    middleware.monitor.log_tool_call.assert_called()

    with pytest.raises(ValueError, match="handler failed"):
        middleware.wrap_tool_call(request("parse_netflow"), lambda _req: (_ for _ in ()).throw(ValueError("handler failed")))

    from cys_core.domain.agents.policies import build_interrupt_on

    assert "run_active_scan" in build_interrupt_on({"run_active_scan": True, "read_repo_metadata": False})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_security_middleware_async_paths(monkeypatch):
    import cys_core.middleware.security_middleware as security_middleware

    middleware = security_middleware.SecurityMiddleware("agent-a", "session-a")

    class FakeRateLimiter:
        def __init__(self):
            self.error: Exception | None = None

        async def acheck(self, _key):
            if self.error:
                raise self.error

    rate_limiter = FakeRateLimiter()
    middleware.rate_limiter = rate_limiter
    middleware.monitor = SimpleNamespace(log_security_event=MagicMock(), log_tool_call=MagicMock())
    monkeypatch.setattr(security_middleware.settings, "stage", "test")

    class HighRisk:
        value = "high"

        def __gt__(self, _other):
            return True

    monkeypatch.setattr(security_middleware, "classify_tool_risk", lambda _name: HighRisk())
    gated = await middleware.awrap_tool_call(request("danger"), lambda req: ToolMessage(content="ok", tool_call_id="x"))
    assert gated.status == "error"

    rate_limiter.error = RuntimeError("too many")
    limited = await middleware.awrap_tool_call(request("parse_netflow"), lambda req: ToolMessage(content="ok", tool_call_id="x"))
    assert limited.status == "error"
    middleware.monitor.log_security_event.assert_called()

    rate_limiter.error = None
    monkeypatch.setattr(security_middleware, "classify_tool_risk", lambda _name: security_middleware.RiskLevel.LOW)

    async def async_handler(req):
        return ToolMessage(content="async-ok", tool_call_id=req.tool_call["id"])

    handled = await middleware.awrap_tool_call(request("parse_netflow"), async_handler)
    assert handled.content == "async-ok"
    middleware.monitor.log_tool_call.assert_called()

    with pytest.raises(ValueError, match="async failed"):
        await middleware.awrap_tool_call(
            request("parse_netflow"),
            lambda _req: (_ for _ in ()).throw(ValueError("async failed")),
        )
