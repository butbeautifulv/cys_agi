from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkerJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerJob(BaseModel):
    """Queued unit of work for an ephemeral worker."""

    job_id: str
    event_id: str
    persona: str
    playbook_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    status: WorkerJobStatus = WorkerJobStatus.PENDING
    sandbox_id: str = ""
    feedback: str = ""


class SandboxCredentials(BaseModel):
    """Credentials returned when a sandbox is provisioned."""

    sandbox_id: str
    endpoint: str = ""
    token: str = ""


class RunResult(BaseModel):
    """Outcome of a single worker run."""

    job_id: str
    persona: str
    success: bool
    finding: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    sandbox_id: str = ""
