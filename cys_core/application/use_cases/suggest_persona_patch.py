from __future__ import annotations

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogSource, PersonaQuality


class SuggestPersonaPatch:
    """Create a draft persona suggestion — never auto-applies to runtime."""

    def __init__(self, catalog: AgentCatalogPort) -> None:
        self._catalog = catalog

    def execute(
        self,
        name: str,
        *,
        description: str,
        system_prompt: str,
        profile_id: str = "cybersec-soc",
    ) -> AgentCatalogEntry:
        draft_name = f"{name}-draft"
        entry = AgentCatalogEntry(
            name=draft_name,
            description=description,
            system_prompt=system_prompt,
            profile_id=profile_id,
            enabled=False,
            source=CatalogSource.API,
            tags=["draft-suggestion"],
            version_tag=f"suggest:{name}",
        )
        return self._catalog.upsert_agent(entry)
