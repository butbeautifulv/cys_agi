from __future__ import annotations

from typing import Any

from cys_core.observability.tracing import get_correlation_id


def build_job_trace_metadata(
    *,
    persona: str,
    job_id: str = "",
    event_id: str = "",
    correlation_id: str = "",
    sandbox_id: str = "",
) -> dict[str, Any]:
    """Langfuse/LangChain trace tags and metadata for a worker job."""
    cid = correlation_id or get_correlation_id() or event_id or job_id
    tags = [f"persona:{persona}"]
    if cid:
        tags.append(f"correlation:{cid}")
    if job_id:
        tags.append(f"job:{job_id}")

    metadata = {
        "persona": persona,
        "job_id": job_id,
        "event_id": event_id,
        "correlation_id": cid,
        "sandbox_id": sandbox_id,
    }
    return {"tags": tags, "metadata": {k: v for k, v in metadata.items() if v}}


def merge_langchain_config(
    base: dict[str, Any],
    *,
    persona: str,
    job_id: str = "",
    event_id: str = "",
    correlation_id: str = "",
    sandbox_id: str = "",
) -> dict[str, Any]:
    trace = build_job_trace_metadata(
        persona=persona,
        job_id=job_id,
        event_id=event_id,
        correlation_id=correlation_id,
        sandbox_id=sandbox_id,
    )
    merged = dict(base)
    merged["metadata"] = {**base.get("metadata", {}), **trace["metadata"]}
    merged["tags"] = [*base.get("tags", []), *trace["tags"]]
    return merged
