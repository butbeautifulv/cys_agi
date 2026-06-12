from __future__ import annotations

import uuid
from typing import Any

from control.job_store import get_job_store
from cys_core.observability.metrics import metrics
from cys_core.domain.workers.models import PendingHitlAction
from cys_core.infrastructure.kafka_paused import publish_paused_job_sync
from tool_gateway.approval import create_approval_id, params_hash


def job_id_from_session(session_id: str) -> str | None:
    parts = session_id.split(":", 2)
    if len(parts) == 3 and parts[0] == "worker":
        return parts[2]
    return None


def build_hitl_preview(
    *,
    tool_name: str,
    tool_args: dict[str, Any],
    risk_level: str,
    session_id: str,
    persona: str,
) -> dict[str, Any]:
    job_id = job_id_from_session(session_id) or session_id
    approval_id = create_approval_id()
    return {
        "action": "tool_call",
        "tool": tool_name,
        "args": tool_args,
        "risk": risk_level,
        "job_id": job_id,
        "session_id": session_id,
        "persona": persona,
        "approval_id": approval_id,
        "params_hash": params_hash(tool_args),
    }


def register_hitl_pause(preview: dict[str, Any]) -> PendingHitlAction:
    pending = PendingHitlAction(
        job_id=preview["job_id"],
        session_id=preview["session_id"],
        persona=preview["persona"],
        tool_name=preview["tool"],
        tool_args=preview.get("args", {}),
        risk_level=preview.get("risk", ""),
        approval_id=preview["approval_id"],
    )
    get_job_store().pause_for_hitl(pending, preview)
    metrics.refresh_hitl_pending(len(get_job_store().list_pending_approvals()))
    publish_paused_job_sync(
        {
            "job_id": pending.job_id,
            "persona": pending.persona,
            "tool": pending.tool_name,
            "approval_id": pending.approval_id,
            "status": "awaiting_approval",
        }
    )
    return pending


def resume_decision_approved(decision: Any) -> bool:
    if isinstance(decision, dict):
        if decision.get("decision") == "reject":
            return False
        if decision.get("decision") in {"approve", "edit"}:
            return True
        decisions = decision.get("decisions", [])
        if decisions and decisions[0].get("type") == "reject":
            return False
        return True
    return bool(decision)
