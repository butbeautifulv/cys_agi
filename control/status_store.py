from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StatusStore:
    """In-memory user-facing status feed."""

    events: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    critic_feedback: list[dict[str, Any]] = field(default_factory=list)
    coordinator_narratives: list[str] = field(default_factory=list)

    def record_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    def record_finding(self, envelope: dict[str, Any]) -> None:
        self.findings.append(envelope)

    def record_critic(self, feedback: dict[str, Any]) -> None:
        self.critic_feedback.append(feedback)

    def record_narrative(self, text: str) -> None:
        self.coordinator_narratives.append(text)

    def snapshot(self) -> dict[str, Any]:
        return {
            "events_count": len(self.events),
            "findings_count": len(self.findings),
            "latest_narrative": self.coordinator_narratives[-1] if self.coordinator_narratives else "",
            "events": self.events[-20:],
            "findings": self.findings[-20:],
            "critic_feedback": self.critic_feedback[-20:],
            "narratives": self.coordinator_narratives[-10:],
        }


_status_store = StatusStore()


def get_status_store() -> StatusStore:
    return _status_store
