from __future__ import annotations

from pydantic import BaseModel

from cys_core.domain.workers.models import WorkerJob


class PersonaBudget(BaseModel):
    max_tokens: int
    max_cost_usd: float
    max_tool_calls: int = 50


PERSONA_BUDGETS: dict[str, PersonaBudget] = {
    "soc": PersonaBudget(max_tokens=50_000, max_cost_usd=2.0),
    "network": PersonaBudget(max_tokens=50_000, max_cost_usd=2.0),
    "compliance": PersonaBudget(max_tokens=40_000, max_cost_usd=1.5),
    "redteam": PersonaBudget(max_tokens=80_000, max_cost_usd=5.0),
    "intel": PersonaBudget(max_tokens=45_000, max_cost_usd=2.0),
    "hunter": PersonaBudget(max_tokens=55_000, max_cost_usd=2.5),
    "identity": PersonaBudget(max_tokens=50_000, max_cost_usd=2.0),
    "dfir": PersonaBudget(max_tokens=60_000, max_cost_usd=3.0),
    "cloud": PersonaBudget(max_tokens=50_000, max_cost_usd=2.0),
    "purple": PersonaBudget(max_tokens=45_000, max_cost_usd=1.5),
    "consultant": PersonaBudget(max_tokens=35_000, max_cost_usd=1.0),
}

DEFAULT_BUDGET = PersonaBudget(max_tokens=40_000, max_cost_usd=2.0)


def persona_budget(persona: str) -> PersonaBudget:
    return PERSONA_BUDGETS.get(persona, DEFAULT_BUDGET)


def enrich_job_budget(job: WorkerJob) -> WorkerJob:
    """Apply persona defaults for unset budget fields."""
    budget = persona_budget(job.persona)
    return job.model_copy(
        update={
            "max_tokens": job.max_tokens or budget.max_tokens,
            "max_cost_usd": job.max_cost_usd or budget.max_cost_usd,
            "max_tool_calls": job.max_tool_calls or budget.max_tool_calls,
        }
    )
