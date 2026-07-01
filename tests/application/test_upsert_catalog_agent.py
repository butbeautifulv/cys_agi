from __future__ import annotations

import pytest

from cys_core.application.use_cases.seed_catalog import SeedCatalog
from cys_core.application.use_cases.upsert_catalog_agent import UpsertCatalogAgent
from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogSource, ProfilePack
from cys_core.infrastructure.catalog.memory import InMemoryAgentCatalog


@pytest.mark.unit
def test_upsert_catalog_agent():
    catalog = InMemoryAgentCatalog()
    saved = UpsertCatalogAgent(catalog).execute("soc", {"description": "d", "role": "worker"})
    assert saved.name == "soc"
    assert catalog.get_agent("soc") is not None


@pytest.mark.unit
def test_seed_catalog():
    catalog = InMemoryAgentCatalog()
    profile = ProfilePack(id="p1", name="Pack", description="d")
    entries = [
        AgentCatalogEntry(
            name="soc",
            description="",
            role="worker",
            profile_id="p1",
            source=CatalogSource.SEED,
        )
    ]

    def _load():
        return profile, entries

    out = SeedCatalog(catalog, load_profile_pack=_load).execute()
    assert out["seeded"] == 1
