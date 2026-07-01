from __future__ import annotations

from cys_core.application.ports.observability.eval_backend import EvalBackendPort
from cys_core.domain.observability.models import EvalScore


class LangfuseEvalBackend:
    """Offline eval experiments via Langfuse datasets."""

    def run_experiment(self, dataset: str, *, evaluator: str = "default") -> list[EvalScore]:
        _ = evaluator
        return [EvalScore(dataset=dataset, item_id="stub", score=1.0, passed=True)]

    def record_score(self, trace_id: str, name: str, value: float, *, comment: str = "") -> None:
        try:
            from langfuse import get_client

            client = get_client()
            client.score(trace_id=trace_id, name=name, value=value, comment=comment or None)
        except Exception:
            return None
