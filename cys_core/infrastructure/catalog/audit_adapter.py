from __future__ import annotations

from typing import Any

from cys_core.application.ports.catalog_audit import CatalogAuditPort
from cys_core.infrastructure.catalog.audit import record_catalog_change


class InMemoryCatalogAudit(CatalogAuditPort):
    def record_change(
        self,
        action: str,
        *,
        agent: str,
        actor: str = "api",
        details: dict[str, Any] | None = None,
    ) -> None:
        record_catalog_change(action, agent=agent, actor=actor, details=details)
