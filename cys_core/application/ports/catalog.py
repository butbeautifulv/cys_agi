from __future__ import annotations

from typing import Protocol

from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogVersion, ProfilePack


class AgentCatalogPort(Protocol):
    def list_agents(self, *, profile_id: str | None = None, enabled_only: bool = True) -> list[AgentCatalogEntry]: ...

    def get_agent(self, name: str) -> AgentCatalogEntry | None: ...

    def upsert_agent(self, entry: AgentCatalogEntry) -> AgentCatalogEntry: ...

    def list_profiles(self) -> list[ProfilePack]: ...

    def get_version(self, profile_id: str) -> CatalogVersion: ...
