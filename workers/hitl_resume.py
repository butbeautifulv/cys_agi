from __future__ import annotations

from typing import Any

from control.job_store import get_job_store
from cys_core.observability.metrics import metrics
from cys_core.domain.workers.models import JobResumeRequest, WorkerJobStatus
from cys_core.runtime.agent import get_runtime
from tool_gateway.approval import params_hash, record_hitl_approval


class HitlResumeError(Exception):
    pass


async def resume_worker_job(job_id: str, request: JobResumeRequest) -> dict[str, Any]:
    store = get_job_store()
    record = store.get(job_id)
    if record is None:
        raise HitlResumeError(f"Unknown job: {job_id}")
    if record.status != WorkerJobStatus.AWAITING_APPROVAL or record.pending_hitl is None:
        raise HitlResumeError(f"Job {job_id} is not awaiting approval")

    pending = record.pending_hitl
    if request.approval_id and request.approval_id != pending.approval_id:
        metrics.record_approval_bypass("invalid_approval_id")
        raise HitlResumeError("Invalid approval_id for high-risk action")

    if request.decision == "reject":
        record_hitl_approval(
            actor=request.actor,
            tool=pending.tool_name,
            persona=pending.persona,
            job_id=job_id,
            decision="reject",
            tool_args=pending.tool_args,
            approval_id=pending.approval_id,
        )
        store.mark_failed(job_id)
        return {"job_id": job_id, "status": "rejected"}

    tool_args = request.edited_args if request.decision == "edit" and request.edited_args else pending.tool_args
    if request.decision == "approve":
        expected_hash = record.hitl_preview.get("params_hash", "")
        if expected_hash and params_hash(tool_args) != expected_hash:
            metrics.record_approval_bypass("params_hash_mismatch")
            raise HitlResumeError("Tool args hash mismatch — approval bypass blocked")

    record_hitl_approval(
        actor=request.actor,
        tool=pending.tool_name,
        persona=pending.persona,
        job_id=job_id,
        decision=request.decision,
        tool_args=tool_args,
        approval_id=pending.approval_id,
    )
    store.mark_running(job_id)

    resume_payload = {"decision": request.decision, "approval_id": pending.approval_id}
    runtime = get_runtime()
    result = await runtime.aresume(record.persona, record.session_id, resume_payload)
    store.mark_completed(job_id)
    return {"job_id": job_id, "status": "resumed", "result": result}
