from __future__ import annotations

from pathlib import Path

from cys_core.domain.events.models import RoutingDecision, SecurityEvent
from cys_core.domain.events.plans import PlanRoutingConfig, load_plans_from_dir, rule_matches


class EventRouter:
    """Deterministic event router — maps events to worker personas via plan rules."""

    def __init__(self, plans: list[PlanRoutingConfig] | None = None) -> None:
        self._plans = plans or []

    @classmethod
    def from_plans_dir(cls, plans_dir: Path) -> EventRouter:
        return cls(load_plans_from_dir(plans_dir))

    def route(self, event: SecurityEvent) -> RoutingDecision:
        personas: list[str] = []
        playbook_id = ""
        notify_control = False
        matched_rules = 0

        for plan in self._plans:
            for rule in plan.rules:
                if not rule_matches(rule, event.type, event.severity):
                    continue
                matched_rules += 1
                for persona in rule.personas:
                    if persona not in personas:
                        personas.append(persona)
                if rule.playbook_id:
                    playbook_id = rule.playbook_id
                elif plan.id and not playbook_id:
                    playbook_id = plan.id
                notify_control = notify_control or rule.notify_control

        if event.severity in ("high", "critical"):
            notify_control = True

        if not personas:
            return RoutingDecision(
                event_id=event.id,
                jobs=[],
                reason="no_matching_rule",
            )

        return RoutingDecision(
            event_id=event.id,
            jobs=[f"{p}:{event.id}" for p in personas],
            playbook_id=playbook_id,
            personas=personas,
            notify_control=notify_control,
            reason=f"matched_{matched_rules}_rules",
        )
