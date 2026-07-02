from __future__ import annotations

from typing import Callable

from bootstrap.catalog_seed_loaders import (
    load_mcp_servers_for_seed,
    load_plans_for_seed,
    load_skills_for_seed,
)
from cys_core.infrastructure.catalog.tool_catalog_seed import load_tools_for_seed
from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.domain.catalog.models import ProfilePack


class SeedCatalog:
    def __init__(
        self,
        catalog: AgentCatalogPort,
        *,
        load_profile_pack: Callable[[], tuple[ProfilePack, list]],
        reload: Callable[[], None] | None = None,
    ) -> None:
        self.catalog = catalog
        self.load_profile_pack = load_profile_pack
        self.reload = reload or (lambda: None)

    def execute(self) -> dict:
        profile, entries = self.load_profile_pack()
        skills = load_skills_for_seed(profile.id)
        plans = load_plans_for_seed(profile.id)
        mcp_servers = load_mcp_servers_for_seed(profile.id)
        tools = load_tools_for_seed(profile.id)
        self.catalog.seed(entries, profile, skills=skills, plans=plans, mcp_servers=mcp_servers)
        from cys_core.infrastructure.catalog.registry_factory import get_tool_catalog

        get_tool_catalog().seed(tools)
        self.reload()
        return {
            "profile": profile.model_dump(),
            "seeded": len(entries),
            "skills": len(skills),
            "plans": len(plans),
            "mcp_servers": len(mcp_servers),
            "tools": len(tools),
        }
