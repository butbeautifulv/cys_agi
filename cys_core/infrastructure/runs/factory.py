from __future__ import annotations

from functools import lru_cache

from cys_core.application.runtime_config import get_postgres_url, get_use_memory_fallback
from cys_core.infrastructure.runs.memory import InMemoryRunStateStore
from cys_core.infrastructure.runs.todo_store import InMemoryWorkTodoStore

_todo_store = InMemoryWorkTodoStore()


@lru_cache
def get_run_state_store():
    if get_use_memory_fallback():
        return InMemoryRunStateStore()
    from cys_core.infrastructure.runs.postgres import PostgresRunStateStore

    return PostgresRunStateStore(get_postgres_url())


def get_work_todo_store():
    return _todo_store
