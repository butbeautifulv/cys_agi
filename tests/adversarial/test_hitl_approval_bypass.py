"""Abuse case: high-risk tool resume requires valid approval_id and args hash."""

import pytest

from control.job_store import JobStore
from cys_core.domain.workers.models import PendingHitlAction
from tool_gateway.approval import params_hash
from workers.hitl_resume import HitlResumeError, resume_worker_job
from cys_core.domain.workers.models import JobResumeRequest


@pytest.mark.adversarial
@pytest.mark.asyncio
async def test_resume_blocks_approval_id_bypass(monkeypatch):
    store = JobStore()
    monkeypatch.setattr("workers.hitl_resume.get_job_store", lambda: store)

    args = {"target": "production"}
    pending = PendingHitlAction(
        job_id="job-bypass",
        session_id="worker:redteam:job-bypass",
        persona="redteam",
        tool_name="run_active_scan",
        tool_args=args,
        approval_id="appr-valid",
    )
    store.pause_for_hitl(pending, {"params_hash": params_hash(args)})

    with pytest.raises(HitlResumeError, match="approval_id"):
        await resume_worker_job(
            "job-bypass",
            JobResumeRequest(decision="approve", approval_id="appr-forged", actor="attacker"),
        )
