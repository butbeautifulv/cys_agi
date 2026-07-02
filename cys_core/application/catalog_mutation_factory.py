from __future__ import annotations

from cys_core.application.catalog_mutation_service import CatalogMutationService
from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog, reload_agent_registry
from cys_core.infrastructure.catalog.registry_factory import (
    get_catalog_audit,
    get_catalog_write_gate,
    get_tool_catalog,
)


def get_catalog_mutation_service(*, reload=None) -> CatalogMutationService:
    return CatalogMutationService(
        write_gate=get_catalog_write_gate(reload=reload),
        agent_catalog=get_agent_catalog(),
        tool_catalog=get_tool_catalog(),
        audit=get_catalog_audit(),
        reload=reload or reload_agent_registry,
    )
