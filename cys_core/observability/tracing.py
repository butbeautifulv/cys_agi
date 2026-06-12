from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def bind_correlation_id(correlation_id: str) -> Token[str]:
    return correlation_id_var.set(correlation_id or "")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def reset_correlation_id(token: Token[str]) -> None:
    correlation_id_var.reset(token)


def inject_correlation_headers(headers: dict[str, str] | None = None) -> dict[str, str]:
    """Propagate correlation_id via HTTP headers and optional OTel trace context."""
    out = dict(headers or {})
    cid = get_correlation_id()
    if cid:
        out["x-correlation-id"] = cid
    return _inject_otel_context(out)


def extract_correlation_id(headers: dict[str, str]) -> str:
    for key in ("x-correlation-id", "X-Correlation-Id", "correlation-id"):
        value = headers.get(key)
        if value:
            return value
    return ""


def _inject_otel_context(headers: dict[str, str]) -> dict[str, str]:
    try:
        from opentelemetry import propagate

        carrier: dict[str, str] = {}
        propagate.inject(carrier)
        headers.update(carrier)
    except Exception:
        return headers
    return headers


def bind_from_headers(headers: dict[str, str]) -> Token[str] | None:
    cid = extract_correlation_id(headers)
    if not cid:
        return None
    return bind_correlation_id(cid)


def structlog_context() -> dict[str, Any]:
    return {"correlation_id": get_correlation_id()}
