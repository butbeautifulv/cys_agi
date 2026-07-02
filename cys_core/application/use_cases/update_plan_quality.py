from __future__ import annotations

from cys_core.application.ports.registry_catalogs import PlanCatalogPort
from cys_core.domain.catalog.models import PlanCatalogEntry


class UpdatePlanQuality:
    def __init__(self, plan_catalog: PlanCatalogPort) -> None:
        self._plans = plan_catalog

    def record_match(self, plan_id: str, *, profile_id: str = "cybersec-soc", jobs: int = 1) -> None:
        entry = self._plans.get_plan(plan_id, profile_id=profile_id)
        if entry is None:
            return
        entry.quality.match_count += 1
        entry.quality.avg_jobs_per_event = (
            (entry.quality.avg_jobs_per_event * max(0, entry.quality.match_count - 1) + jobs)
            / max(1, entry.quality.match_count)
        )
        self._plans.upsert_plan(entry)
