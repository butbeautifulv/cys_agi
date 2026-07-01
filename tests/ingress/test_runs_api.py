from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from interfaces.api.app import create_app


@pytest.fixture
def client(monkeypatch):
    class FakeRuntime:
        async def arun(self, name, user_input, **kwargs):
            if "plan" in user_input.lower() or '"mode": "plan"' in user_input:
                return {"plan": {"rationale": "steps", "proposed_workers": ["soc"], "todos": []}}
            return {"status": "ok", "message": user_input}

    monkeypatch.setattr("interfaces.api.runs.get_runtime", lambda: FakeRuntime())
    return TestClient(create_app())


@pytest.mark.unit
def test_create_run_and_step(client):
    created = client.post("/runs", json={"goal": "investigate", "persona": "conductor"})
    assert created.status_code == 200
    run_id = created.json()["run_context"]["context_id"]
    stepped = client.post(f"/runs/{run_id}/steps", json={"message": "continue"})
    assert stepped.status_code == 200
    fetched = client.get(f"/runs/{run_id}")
    assert fetched.status_code == 200


@pytest.mark.unit
def test_approve_plan(client):
    created = client.post("/runs", json={"goal": "plan task", "mode": "plan"})
    assert created.status_code == 200
    run_id = created.json()["run_context"]["context_id"]
    approved = client.post(f"/runs/{run_id}/approve-plan", json={"decision": "approve"})
    assert approved.status_code == 200
