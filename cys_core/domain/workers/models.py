from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkerJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
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
    max_tokens: int = 0
    max_cost_usd: float = 0.0
    max_tool_calls: int = 0


class SandboxCredentials(BaseModel):
    """Credentials returned when a sandbox is provisioned."""

    sandbox_id: str
    endpoint: str = ""
    token: str = ""


class PendingHitlAction(BaseModel):
    """Tool call waiting for human approval."""

    job_id: str
    session_id: str
    persona: str
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = ""
    approval_id: str = ""


class JobResumeRequest(BaseModel):
    """Resume payload for a paused worker job."""

    decision: str  # approve | reject | edit
    edited_args: dict[str, Any] = Field(default_factory=dict)
    approval_id: str = ""
    actor: str = "operator"


class RunResult(BaseModel):
    """Outcome of a single worker run."""

    job_id: str
    persona: str
    success: bool
    finding: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    sandbox_id: str = ""
