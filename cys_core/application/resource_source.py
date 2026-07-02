from __future__ import annotations

from typing import Protocol

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.application.runtime_config import get_use_dynamic_catalog
from cys_core.domain.catalog.profile_id import DEFAULT_PROFILE_ID
from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog
from cys_core.registry.agents import AgentRegistry
from cys_core.registry.skill_registry import SkillRegistry


class ResourceSource(Protocol):
    def list_worker_personas(self, *, profile_id: str = DEFAULT_PROFILE_ID) -> list[str]: ...

    def search_skills(self, query: str, *, profile_id: str = DEFAULT_PROFILE_ID, limit: int = 5) -> list[dict]: ...


class CatalogSource:
    def __init__(self, catalog: AgentCatalogPort | None = None) -> None:
        self._catalog = catalog

    def _catalog_or_get(self) -> AgentCatalogPort:
        return self._catalog or get_agent_catalog()

    def list_worker_personas(self, *, profile_id: str = DEFAULT_PROFILE_ID) -> list[str]:
        catalog = self._catalog_or_get()
        return [
            entry.name
            for entry in catalog.list_agents(profile_id=profile_id, enabled_only=True)
            if entry.role in ("worker", "specialist")
        ]

    def search_skills(self, query: str, *, profile_id: str = DEFAULT_PROFILE_ID, limit: int = 5) -> list[dict]:
        from cys_core.infrastructure.catalog.registry_factory import get_skill_catalog

        q = query.lower()
        hits = [
            entry
            for entry in get_skill_catalog().list_skills(profile_id=profile_id, enabled_only=True)
            if q in entry.id or q in (entry.description or "").lower()
        ]
        return [{"id": entry.id, "description": entry.description} for entry in hits[:limit]]


class FilesystemSource:
    def list_worker_personas(self, *, profile_id: str = DEFAULT_PROFILE_ID) -> list[str]:
        del profile_id
        registry = AgentRegistry.load()
        return [
            defn.name
            for defn in registry.all()
            if defn.role in ("worker", "specialist")
        ]

    def search_skills(self, query: str, *, profile_id: str = DEFAULT_PROFILE_ID, limit: int = 5) -> list[dict]:
        del profile_id
        reg = SkillRegistry.load()
        q = query.lower()
        hits = [sid for sid in reg.names() if q in sid or q in (reg.get(sid).description or "").lower()]
        return [{"id": sid, "description": reg.get(sid).description} for sid in hits[:limit]]


def get_resource_source(*, catalog: AgentCatalogPort | None = None) -> ResourceSource:
    if get_use_dynamic_catalog():
        return CatalogSource(catalog)
    return FilesystemSource()
