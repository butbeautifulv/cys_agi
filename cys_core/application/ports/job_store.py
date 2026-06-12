from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from cys_core.domain.workers.models import PendingHitlAction, WorkerJobStatus


@dataclass
class JobRecord:
    job_id: str
    session_id: str
    persona: str
    status: WorkerJobStatus = WorkerJobStatus.RUNNING
    hitl_preview: dict[str, Any] = field(default_factory=dict)
    pending_hitl: PendingHitlAction | None = None


class JobStorePort(Protocol):
    def upsert_running(self, job_id: str, session_id: str, persona: str) -> JobRecord: ...

    def pause_for_hitl(self, pending: PendingHitlAction, preview: dict[str, Any]) -> JobRecord: ...

    def get(self, job_id: str) -> JobRecord | None: ...

    def mark_running(self, job_id: str) -> JobRecord | None: ...

    def mark_completed(self, job_id: str) -> None: ...

    def mark_failed(self, job_id: str) -> None: ...

    def list_pending_approvals(self) -> list[PendingHitlAction]: ...
