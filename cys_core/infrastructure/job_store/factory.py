from __future__ import annotations

from bootstrap.settings import Settings, get_settings
from cys_core.application.ports.job_store import JobStorePort
from cys_core.domain.persistence.exceptions import PersistenceUnavailableError
from cys_core.infrastructure.job_store.in_memory import InMemoryJobStore
from cys_core.infrastructure.job_store.postgres import PostgresJobStore

_job_store: JobStorePort | None = None


def _use_postgres_job_store(settings: Settings) -> bool:
    connector = settings.job_store_connector.lower()
    if connector == "memory":
        return False
    if connector == "postgres":
        return True
    return not settings.use_memory_fallback and settings.stage != "test"


def get_job_store(settings: Settings | None = None) -> JobStorePort:
    global _job_store
    active = settings or get_settings()
    if _job_store is not None:
        return _job_store
    if _use_postgres_job_store(active):
        try:
            _job_store = PostgresJobStore(active.postgres_url)
            return _job_store
        except Exception as exc:
            if active.stage == "prod" and not active.use_memory_fallback:
                raise PersistenceUnavailableError("Postgres job store unavailable") from exc
    _job_store = InMemoryJobStore()
    return _job_store


def reset_job_store() -> None:
    global _job_store
    _job_store = None
