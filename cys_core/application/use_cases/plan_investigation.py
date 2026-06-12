from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import BaseModel, Field

from cys_core.application.ports.memory import InvestigationStateStore
from cys_core.domain.events.models import SecurityEvent
from cys_core.domain.memory.models import InvestigationState


class InvestigationPlan(BaseModel):
    personas: list[str] = Field(default_factory=list)
    sub_goals: dict[str, str] = Field(default_factory=dict)
    rationale: str = ""


class PlannerRuntime(Protocol):
    async def arun(
        self,
        name: str,
        user_input: str,
        *,
        session_id: str | None = None,
        tenant_id: str | None = None,
        investigation_id: str | None = None,
    ) -> dict[str, Any]: ...


class PlanInvestigation:
    """LLM planner for manual.investigation events — produces ordered persona plan."""

    DEFAULT_PERSONAS = ["soc", "network", "compliance"]

    def __init__(
        self,
        *,
        runtime: PlannerRuntime,
        investigation_store: InvestigationStateStore,
        planner_persona: str = "planner",
    ) -> None:
        self.runtime = runtime
        self.investigation_store = investigation_store
        self.planner_persona = planner_persona

    def _parse_plan(self, result: dict[str, Any], goal: str) -> InvestigationPlan:
        if "personas" in result and isinstance(result["personas"], list):
            personas = [str(item) for item in result["personas"]]
            sub_goals = result.get("sub_goals", {})
            if not isinstance(sub_goals, dict):
                sub_goals = {}
            return InvestigationPlan(
                personas=personas,
                sub_goals={str(k): str(v) for k, v in sub_goals.items()},
                rationale=str(result.get("rationale", "")),
            )
        raw = result.get("raw_response", "")
        if raw:
            try:
                parsed = json.loads(raw)
                return self._parse_plan(parsed, goal)
            except json.JSONDecodeError:
                pass
        return InvestigationPlan(
            personas=list(self.DEFAULT_PERSONAS),
            sub_goals={persona: goal for persona in self.DEFAULT_PERSONAS},
            rationale="fallback_default_plan",
        )

    async def execute(self, event: SecurityEvent) -> InvestigationPlan:
        goal = str(event.payload.get("goal", event.payload.get("message", "Investigate security incident")))
        investigation_id = event.correlation_id or event.id
        prompt = json.dumps(
            {
                "goal": goal,
                "event_type": event.type,
                "severity": event.severity,
                "available_personas": self.DEFAULT_PERSONAS,
                "instructions": (
                    "Return JSON with keys: personas (ordered list), sub_goals (map persona->task), rationale."
                ),
            },
            ensure_ascii=False,
        )
        try:
            result = await self.runtime.arun(
                self.planner_persona,
                prompt,
                session_id=f"planner:{investigation_id}",
                tenant_id=event.tenant_id,
                investigation_id=investigation_id,
            )
            plan = self._parse_plan(result, goal)
        except Exception:
            plan = InvestigationPlan(
                personas=list(self.DEFAULT_PERSONAS),
                sub_goals={persona: goal for persona in self.DEFAULT_PERSONAS},
                rationale="planner_unavailable_fallback",
            )

        if not plan.personas:
            plan.personas = list(self.DEFAULT_PERSONAS)

        state = self.investigation_store.get(event.tenant_id, investigation_id)
        if state is None:
            state = InvestigationState(
                investigation_id=investigation_id,
                tenant_id=event.tenant_id,
                goal=goal,
                status="in_progress",
            )
        state.planner_plan = plan.personas
        state.goal = goal
        self.investigation_store.upsert(state)
        return plan

    def to_worker_jobs_payload(self, plan: InvestigationPlan) -> dict[str, Any]:
        return {
            "planner_plan": plan.personas,
            "sub_goals": plan.sub_goals,
            "rationale": plan.rationale,
        }
