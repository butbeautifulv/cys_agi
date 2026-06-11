from __future__ import annotations

import uuid
from functools import lru_cache

from cys_core.domain.workers.models import SandboxCredentials


class LocalSandboxConnector:
    """In-process sandbox stub for dev/test — simulates ephemeral worker isolation."""

    name = "local"

    def __init__(self) -> None:
        self._active: dict[str, SandboxCredentials] = {}

    def create(self, run_id: str, persona: str, policy: str = "default") -> SandboxCredentials:
        creds = SandboxCredentials(
            sandbox_id=f"local-{run_id}-{uuid.uuid4().hex[:8]}",
            endpoint=f"sandbox://local/{persona}/{run_id}",
            token=f"tok-{policy}-{run_id}",
        )
        self._active[run_id] = creds
        return creds

    def destroy(self, run_id: str) -> None:
        self._active.pop(run_id, None)

    async def acreate(self, run_id: str, persona: str, policy: str = "default") -> SandboxCredentials:
        return self.create(run_id, persona, policy)

    async def adestroy(self, run_id: str) -> None:
        self.destroy(run_id)

    def is_active(self, run_id: str) -> bool:
        return run_id in self._active


@lru_cache
def get_sandbox_connector() -> LocalSandboxConnector:
    return LocalSandboxConnector()
