from __future__ import annotations

import uuid

from config import settings
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


_sandbox_connector: LocalSandboxConnector | None = None


def get_sandbox_connector() -> LocalSandboxConnector:
    """Return sandbox connector; K8s when SANDBOX_CONNECTOR=k8s."""
    global _sandbox_connector
    if _sandbox_connector is not None:
        return _sandbox_connector
    if settings.sandbox_connector == "k8s":
        from cys_core.infrastructure.k8s_sandbox import K8sSandboxConnector

        _sandbox_connector = K8sSandboxConnector()
    else:
        _sandbox_connector = LocalSandboxConnector()
    return _sandbox_connector


def reset_sandbox_connector_cache() -> None:
    global _sandbox_connector
    _sandbox_connector = None
