from __future__ import annotations

from cys_core.domain.catalog.models import AgentCatalogEntry
from cys_core.domain.policy.defaults import PERSONA_BUDGETS
from cys_core.domain.policy.pure import persona_budget_pure
from cys_core.domain.workers.models import DEFAULT_BUDGET, PersonaBudget, WorkerJob


def persona_budget(persona: str, entry: AgentCatalogEntry | None = None) -> PersonaBudget:
    if entry is None:
        try:
            from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog

            entry = get_agent_catalog().get_agent(persona)
        except Exception:
            entry = None
    return persona_budget_pure(persona, entry)


def enrich_job_budget(job: WorkerJob) -> WorkerJob:
    budget = persona_budget(job.persona)
    return job.model_copy(
        update={
            "max_tokens": job.max_tokens or budget.max_tokens,
            "max_cost_usd": job.max_cost_usd or budget.max_cost_usd,
            "max_tool_calls": job.max_tool_calls or budget.max_tool_calls,
        }
    )


__all__ = ["PERSONA_BUDGETS", "DEFAULT_BUDGET", "PersonaBudget", "persona_budget", "enrich_job_budget"]
