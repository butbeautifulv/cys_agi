from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator

from cys_core.domain.events.models import SecurityEvent, Severity


# Raw SIEM event types from external sources
SIEM_TYPE_MAP: dict[str, str] = {
    # Splunk-style
    "alert": "siem.alert",
    "siem.alert": "siem.alert",
    # EDR
    "edr": "edr.alert",
    "edr.alert": "edr.alert",
    "endpoint.alert": "edr.alert",
    # IAM
    "iam": "iam.event",
    "iam.event": "iam.event",
    "auth.event": "iam.event",
    # Network
    "netflow": "netflow.beacon",
    "netflow.beacon": "netflow.beacon",
    "network.beacon": "netflow.beacon",
    # DNS
    "dns": "dns.anomaly",
    "dns.anomaly": "dns.anomaly",
    # Default fallback
    "default": "siem.alert",
}

SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "informational": "info",
    "warning": "medium",
    "warn": "medium",
    "error": "high",
    "unknown": "medium",
}


class RawSiemEvent(BaseModel):
    """Raw event from SIEM API (Splunk/Elastic-compatible schema)."""

    raw_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str = "alert"
    severity: str = "medium"
    source: str = ""
    host: str = ""
    message: str = ""
    timestamp: str = ""
    tenant_id: str = "default"
    correlation_id: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: str) -> str:
        return SEVERITY_MAP.get(str(v).lower(), "medium")


def normalize_event_type(raw_type: str) -> str:
    """Map raw SIEM event type to internal EventType."""
    return SIEM_TYPE_MAP.get(raw_type.lower().strip(), SIEM_TYPE_MAP["default"])


def raw_to_security_event(raw: RawSiemEvent) -> SecurityEvent:
    """Normalize a raw SIEM event to a SecurityEvent."""
    event_type = normalize_event_type(raw.event_type)
    payload = {
        "host": raw.host,
        "message": raw.message,
        "timestamp": raw.timestamp,
        **raw.extra,
    }
    # Remove empty fields from payload
    payload = {k: v for k, v in payload.items() if v}

    return SecurityEvent(
        id=f"siem-{raw.raw_id}",
        type=event_type,  # type: ignore[arg-type]
        source=raw.source or raw.host or "siem",
        severity=raw.severity,  # type: ignore[arg-type]
        payload=payload,
        tenant_id=raw.tenant_id,
        correlation_id=raw.correlation_id,
    )
