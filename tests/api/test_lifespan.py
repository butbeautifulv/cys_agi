from __future__ import annotations

import pytest

from interfaces.api.app import create_app


@pytest.mark.unit
def test_lifespan_flushes_trace_backend(monkeypatch):
    calls: list[str] = []

    class FakeBackend:
        def flush(self):
            calls.append("flush")

        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(
        "interfaces.api.app.get_container",
        lambda: type("C", (), {"get_trace_backend": lambda self: FakeBackend()})(),
    )
    monkeypatch.setattr("interfaces.api.app.setup_otel", lambda **_: None)
    monkeypatch.setattr("interfaces.api.app.refresh_platform_gauges", lambda: None)

    from fastapi.testclient import TestClient

    with TestClient(create_app()) as client:
        client.get("/health")
    assert "flush" in calls
    assert "shutdown" in calls
