from __future__ import annotations

from typing import Callable

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
        self.catalog.seed(entries, profile)
        self.reload()
        return {"profile": profile.model_dump(), "seeded": len(entries)}
