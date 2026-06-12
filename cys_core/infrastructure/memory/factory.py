from __future__ import annotations

from functools import lru_cache

from bootstrap.settings import Settings, get_settings
from cys_core.application.ports.memory import EpisodicMemoryStore, InvestigationStateStore
from cys_core.domain.persistence.exceptions import PersistenceUnavailableError
from cys_core.infrastructure.memory.stores import (
    InMemoryEpisodicMemoryStore,
    InMemoryInvestigationStateStore,
    PostgresEpisodicMemoryStore,
    PostgresInvestigationStateStore,
)
from cys_core.observability.metrics import metrics

_episodic_store: EpisodicMemoryStore | None = None
_investigation_store: InvestigationStateStore | None = None


def _use_postgres_memory(settings: Settings) -> bool:
    return not settings.use_memory_fallback and settings.stage != "test"


def get_episodic_memory_store(settings: Settings | None = None) -> EpisodicMemoryStore:
    global _episodic_store
    active = settings or get_settings()
    if _episodic_store is not None:
        return _episodic_store
    if _use_postgres_memory(active):
        try:
            _episodic_store = PostgresEpisodicMemoryStore(active.postgres_url)
            return _episodic_store
        except Exception as exc:
            if active.stage == "prod" and not active.use_memory_fallback:
                raise PersistenceUnavailableError("Postgres episodic memory unavailable") from exc
            metrics.record_persistence_fallback("episodic_memory")
    _episodic_store = InMemoryEpisodicMemoryStore()
    return _episodic_store


def get_investigation_state_store(settings: Settings | None = None) -> InvestigationStateStore:
    global _investigation_store
    active = settings or get_settings()
    if _investigation_store is not None:
        return _investigation_store
    if _use_postgres_memory(active):
        try:
            _investigation_store = PostgresInvestigationStateStore(active.postgres_url)
            return _investigation_store
        except Exception as exc:
            if active.stage == "prod" and not active.use_memory_fallback:
                raise PersistenceUnavailableError("Postgres investigation state unavailable") from exc
            metrics.record_persistence_fallback("investigation_state")
    _investigation_store = InMemoryInvestigationStateStore()
    return _investigation_store


def reset_memory_stores() -> None:
    """Clear singletons — for tests."""
    global _episodic_store, _investigation_store
    _episodic_store = None
    _investigation_store = None


@lru_cache
def get_memory_write_service():
    from cys_core.domain.memory.services import MemoryWriteService

    return MemoryWriteService(get_episodic_memory_store())


@lru_cache
def get_memory_read_service():
    from cys_core.domain.memory.services import MemoryReadService

    return MemoryReadService(get_episodic_memory_store())
