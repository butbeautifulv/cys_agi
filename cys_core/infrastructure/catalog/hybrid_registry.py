from __future__ import annotations

import threading

import psycopg

from cys_core.application.runtime_config import (
    get_postgres_url,
    get_use_dynamic_catalog,
    get_use_memory_fallback,
)
from cys_core.application.ports.agent_definitions import AgentDefinitionsLoaderPort
from cys_core.domain.agents.models import AgentDefinition
from cys_core.domain.catalog.models import AgentCatalogEntry
from cys_core.infrastructure.catalog.memory import InMemoryAgentCatalog

_definitions_loader: AgentDefinitionsLoaderPort | None = None
_entry_to_definition: object | None = None

_CATALOG_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agent_catalog (
    name TEXT NOT NULL,
    profile_id TEXT NOT NULL DEFAULT 'cybersec-soc',
    payload JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (name, profile_id)
);
CREATE TABLE IF NOT EXISTS profile_packs (
    id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_catalog_singleton: InMemoryAgentCatalog | None = None
_catalog_lock = threading.Lock()
_registry_cache: object | None = None
_catalog_version: int = 0
_bus_reload_callback: object | None = None


def register_definitions_loader(loader: AgentDefinitionsLoaderPort) -> None:
    global _definitions_loader
    _definitions_loader = loader


def register_entry_to_definition(fn) -> None:
    global _entry_to_definition
    _entry_to_definition = fn


def register_bus_reload_callback(callback) -> None:
    global _bus_reload_callback
    _bus_reload_callback = callback


def get_agent_catalog():
    global _catalog_singleton
    with _catalog_lock:
        if _catalog_singleton is None:
            if get_use_dynamic_catalog() and not get_use_memory_fallback():
                from cys_core.infrastructure.catalog.postgres import PostgresAgentCatalog

                _catalog_singleton = PostgresAgentCatalog(get_postgres_url())
            else:
                _catalog_singleton = InMemoryAgentCatalog()
        return _catalog_singleton


def ensure_catalog_schema(conn: psycopg.Connection) -> None:
    conn.execute(_CATALOG_SCHEMA_SQL)
    conn.commit()


def load_hybrid_registry(root=None):
    """DB/catalog override merged with filesystem definitions."""
    from cys_core.registry.agents import AgentRegistry

    global _registry_cache, _catalog_version
    if get_use_dynamic_catalog():
        if _entry_to_definition is None:
            raise RuntimeError("entry_to_definition not configured")
        catalog = get_agent_catalog()
        if _definitions_loader is None:
            raise RuntimeError("Agent definitions loader not configured")
        fs_agents = _definitions_loader.load(root)
        merged: dict[str, AgentDefinition] = {}
        for name, defn in fs_agents.items():
            merged[name] = defn
        for entry in catalog.list_agents(enabled_only=True):
            merged[entry.name] = _entry_to_definition(entry)
        _registry_cache = AgentRegistry(merged)
        _catalog_version = max((catalog.get_version("cybersec-soc").version, 1))
        from cys_core.observability.metrics import metrics

        metrics.catalog_version.set(_catalog_version)
        return _registry_cache
    return AgentRegistry.load(root)


def reload_agent_registry():
    global _registry_cache
    from cys_core.registry.agents import get_agent_registry

    get_agent_registry.cache_clear()
    _registry_cache = load_hybrid_registry()
    if _bus_reload_callback is not None:
        try:
            _bus_reload_callback(get_agent_registry())
        except Exception:
            pass
    return _registry_cache


def get_catalog_version_metric() -> int:
    return _catalog_version
