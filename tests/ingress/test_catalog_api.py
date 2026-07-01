from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from interfaces.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.mark.unit
def test_catalog_list_and_profiles(client):
    listed = client.get("/catalog/agents")
    assert listed.status_code == 200
    assert "agents" in listed.json()
    profiles = client.get("/catalog/profiles")
    assert profiles.status_code == 200
    assert "profiles" in profiles.json()


@pytest.mark.unit
def test_catalog_put_and_audit(client):
    put = client.put(
        "/catalog/agents/test-agent",
        json={"description": "demo", "role": "worker", "tools": [], "skills": []},
    )
    assert put.status_code == 200
    assert put.json()["name"] == "test-agent"
    got = client.get("/catalog/agents/test-agent")
    assert got.status_code == 200
    audit = client.get("/catalog/audit")
    assert audit.status_code == 200


@pytest.mark.unit
def test_catalog_seed(client):
    seeded = client.post("/catalog/seed")
    assert seeded.status_code == 200
    assert seeded.json()["seeded"] >= 0
