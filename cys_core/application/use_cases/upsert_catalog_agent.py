from __future__ import annotations

from typing import Callable

from cys_core.application.ports.catalog import AgentCatalogPort
from cys_core.application.ports.catalog_audit import CatalogAuditPort
from cys_core.domain.catalog.models import AgentCatalogEntry, CatalogSource
from cys_core.registry.schemas import schema_registry


class UpsertCatalogAgent:
    def __init__(
        self,
        catalog: AgentCatalogPort,
        *,
        reload: Callable[[], None] | None = None,
        record_audit: Callable[..., None] | None = None,
    ) -> None:
        self.catalog = catalog
        self.reload = reload or (lambda: None)
        self.record_audit = record_audit

    def execute(
        self,
        name: str,
        body: dict,
        *,
        actor: str = "api",
    ) -> AgentCatalogEntry:
        if body.get("output_schema"):
            schema_registry.get(body["output_schema"])
        existing = self.catalog.get_agent(name)
        entry = AgentCatalogEntry(
            name=name,
            description=body.get("description", ""),
            role=body.get("role", "worker"),
            output_schema=body.get("output_schema"),
            tools=body.get("tools", []),
            skills=body.get("skills", []),
            trust_level=body.get("trust_level", "internal"),
            bus_recipients=body.get("bus_recipients", []),
            enabled=body.get("enabled", True),
            profile_id=body.get("profile_id", "cybersec-soc"),
            system_prompt=existing.system_prompt if existing else "",
            system_prompt_digest=existing.system_prompt_digest if existing else "",
            source=CatalogSource.API,
        )
        saved = self.catalog.upsert_agent(entry)
        if self.record_audit is not None:
            self.record_audit("upsert", agent=name, actor=actor, details={"version": saved.version})
        self.reload()
        return saved
