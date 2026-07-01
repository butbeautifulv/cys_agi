from __future__ import annotations

import pytest

from cys_core.domain.catalog.models import AgentCatalogEntry, CapabilityBinding, CatalogSource, ProfilePack


@pytest.mark.unit
def test_agent_catalog_entry_defaults():
    entry = AgentCatalogEntry(name="soc", description="SOC analyst")
    assert entry.source == CatalogSource.FILESYSTEM
    assert entry.enabled is True
    assert entry.profile_id == "cybersec-soc"


@pytest.mark.unit
def test_profile_pack_and_capability_binding():
    pack = ProfilePack(id="cybersec-soc", name="Cybersec SOC", default_personas=["soc"])
    binding = CapabilityBinding(capability_id="query_siem", capability_type="tool")
    assert pack.default_personas == ["soc"]
    assert binding.trust_tier == "builtin"
