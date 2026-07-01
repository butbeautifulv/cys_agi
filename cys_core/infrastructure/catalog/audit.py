from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

_audit_log: list[dict[str, Any]] = []
_lock = threading.Lock()


def record_catalog_change(action: str, *, agent: str, actor: str = "api", details: dict[str, Any] | None = None) -> None:
    with _lock:
        _audit_log.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "agent": agent,
                "actor": actor,
                "details": details or {},
            }
        )


def list_catalog_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        return list(reversed(_audit_log[-limit:]))
