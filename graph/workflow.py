"""Deprecated batch LangGraph assessment pipeline.

Replaced by event-driven ingress (ingress/router.py) and worker orchestrator (workers/orchestrator.py).
Kept for backward-compatible imports only.
"""

from __future__ import annotations

import warnings
from typing import Any

warnings.warn(
    "graph.workflow.run_assessment is deprecated; use ingress.router.EventIngress instead",
    DeprecationWarning,
    stacklevel=2,
)


async def run_assessment_async(
    user_input: str,
    *,
    thread_id: str = "assessment-001",
    scope: dict[str, Any] | None = None,
    persistence: Any = None,
    resume: bool | dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ingress.router import get_event_ingress as _get_event_ingress

    ingress = _get_event_ingress()
    event, decision, job_ids = await ingress.aingest(
        "manual.investigation",
        {"raw_input": user_input, "scope": scope or {}},
        correlation_id=thread_id,
    )
    return {
        "deprecated": True,
        "event": event.model_dump(),
        "routing": decision.model_dump(),
        "job_ids": job_ids,
        "resume": resume,
    }


def run_assessment(
    user_input: str,
    *,
    thread_id: str = "assessment-001",
    scope: dict[str, Any] | None = None,
    persistence: Any = None,
    resume: bool | dict[str, Any] | None = None,
) -> dict[str, Any]:
    import asyncio

    return asyncio.run(
        run_assessment_async(
            user_input,
            thread_id=thread_id,
            scope=scope,
            persistence=persistence,
            resume=resume,
        )
    )


async def build_assessment_graph_async(persistence: Any = None):
    warnings.warn("build_assessment_graph_async is deprecated", DeprecationWarning, stacklevel=2)
    return None


def build_assessment_graph(persistence: Any = None):
    warnings.warn("build_assessment_graph is deprecated", DeprecationWarning, stacklevel=2)
    return None
