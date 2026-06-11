from __future__ import annotations

import pytest

from connectors.siem_poll.models import (
    RawSiemEvent,
    normalize_event_type,
    raw_to_security_event,
)


def test_normalize_event_type_known():
    assert normalize_event_type("alert") == "siem.alert"
    assert normalize_event_type("edr") == "edr.alert"
    assert normalize_event_type("netflow") == "netflow.beacon"
    assert normalize_event_type("dns") == "dns.anomaly"
    assert normalize_event_type("iam") == "iam.event"


def test_normalize_event_type_unknown_defaults_to_siem_alert():
    assert normalize_event_type("unknown_type") == "siem.alert"


def test_normalize_event_type_case_insensitive():
    assert normalize_event_type("ALERT") == "siem.alert"
    assert normalize_event_type("EDR.Alert") == "edr.alert"


def test_raw_siem_event_severity_normalization():
    r = RawSiemEvent(severity="CRITICAL")
    assert r.severity == "critical"

    r = RawSiemEvent(severity="informational")
    assert r.severity == "info"

    r = RawSiemEvent(severity="WARNING")
    assert r.severity == "medium"


def test_raw_to_security_event_basic():
    raw = RawSiemEvent(
        raw_id="abc123",
        event_type="alert",
        severity="high",
        source="splunk",
        host="server-01",
        message="Suspicious process",
        tenant_id="acme",
    )
    event = raw_to_security_event(raw)
    assert event.id == "siem-abc123"
    assert event.type == "siem.alert"
    assert event.severity == "high"
    assert event.source == "splunk"
    assert event.tenant_id == "acme"
    assert event.payload["host"] == "server-01"
    assert event.payload["message"] == "Suspicious process"


def test_raw_to_security_event_uses_host_as_source_fallback():
    raw = RawSiemEvent(
        raw_id="xyz",
        event_type="edr.alert",
        host="endpoint-42",
        source="",
    )
    event = raw_to_security_event(raw)
    assert event.source == "endpoint-42"


def test_raw_to_security_event_empty_payload_fields_removed():
    raw = RawSiemEvent(raw_id="test", event_type="alert", host="", message="", timestamp="")
    event = raw_to_security_event(raw)
    # Empty strings should be removed from payload
    assert "host" not in event.payload
    assert "message" not in event.payload


def test_raw_to_security_event_extra_fields():
    raw = RawSiemEvent(
        raw_id="e1",
        event_type="iam.event",
        extra={"user": "admin", "action": "login", "ip": "10.0.0.1"},
    )
    event = raw_to_security_event(raw)
    assert event.payload["user"] == "admin"
    assert event.payload["action"] == "login"
    assert event.payload["ip"] == "10.0.0.1"


def test_raw_siem_event_auto_id():
    r1 = RawSiemEvent()
    r2 = RawSiemEvent()
    assert r1.raw_id != r2.raw_id


def test_correlation_id_preserved():
    raw = RawSiemEvent(raw_id="c1", event_type="alert", correlation_id="corr-999")
    event = raw_to_security_event(raw)
    assert event.correlation_id == "corr-999"
