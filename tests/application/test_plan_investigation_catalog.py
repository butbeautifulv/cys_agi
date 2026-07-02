from __future__ import annotations

import pytest

from cys_core.application.use_cases.plan_investigation import PlanInvestigation
from cys_core.domain.catalog.models import AgentCatalogEntry, ProfilePack, ProfilePolicyPayload
from cys_core.infrastructure.catalog.memory import InMemoryAgentCatalog


class _Runtime:
    async def arun(self, *args, **kwargs):
        return {"personas": ["soc", "unknown-persona"], "sub_goals": {}, "rationale": "test"}


@pytest.mark.unit
def test_planner_filters_to_catalog_personas(monkeypatch):
    catalog = InMemoryAgentCatalog()
    catalog.seed(
        [
            AgentCatalogEntry(name="soc", role="worker", enabled=True),
            AgentCatalogEntry(name="consultant", role="worker", enabled=True),
        ],
        ProfilePack(id="cybersec-soc", name="SOC", policy=ProfilePolicyPayload()),
    )
    monkeypatch.setattr("cys_core.application.resource_source.get_use_dynamic_catalog", lambda: True)
    monkeypatch.setattr("cys_core.application.resource_source.get_agent_catalog", lambda: catalog)

    planner = PlanInvestigation(runtime=_Runtime(), investigation_store=_FakeStore(), profile_id="cybersec-soc")
    available = planner._available_personas()
    assert "soc" in available
    assert "consultant" in available


class _FakeStore:
    def get(self, tenant_id, investigation_id):
        return None

    def upsert(self, state):
        return None
