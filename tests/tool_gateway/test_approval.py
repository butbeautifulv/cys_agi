from __future__ import annotations

import pytest

from tool_gateway.approval import (
    clear_approval_records,
    get_approval_records,
    params_hash,
    record_hitl_approval,
    validate_resume_approval,
)


@pytest.mark.unit
def test_params_hash_stable():
    args = {"target": "example.com", "mode": "safe"}
    assert params_hash(args) == params_hash({"mode": "safe", "target": "example.com"})


@pytest.mark.unit
def test_record_hitl_approval():
    clear_approval_records()
    record = record_hitl_approval(
        actor="alice",
        tool="run_active_scan",
        persona="redteam",
        job_id="job-1",
        decision="approve",
        tool_args={"target": "lab.local"},
    )
    assert record.approval_id.startswith("appr-")
    assert len(get_approval_records()) == 1
    clear_approval_records()


@pytest.mark.unit
def test_validate_resume_approval_blocks_wrong_id():
    args = {"target": "x"}
    digest = params_hash(args)
    assert validate_resume_approval("appr-1", "appr-2", args, digest) is False
    assert validate_resume_approval("appr-1", "appr-1", args, digest) is True
