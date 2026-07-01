from __future__ import annotations

from bootstrap.settings import settings
from cys_core.application.ports.observability.judge_backend import JudgeBackendPort
from cys_core.domain.observability.models import JudgeRequest, JudgeResult


class LangfuseJudgeBackend:
    """LLM-as-judge via configured model (Langfuse-managed rubric ref)."""

    def judge(self, request: JudgeRequest) -> JudgeResult:
        if not settings.langfuse_enabled:
            return JudgeResult(score=0.0, verdict="disabled", reasoning="langfuse disabled")
        try:
            from cys_core.llm import get_model

            model = get_model()
            prompt = (
                f"Rubric: {request.rubric_ref.name}\n"
                f"Input: {request.input_text}\n"
                f"Output: {request.output_text}\n"
                "Return JSON: score 0-1, verdict, reasoning."
            )
            response = model.invoke(prompt)
            content = getattr(response, "content", str(response))
            return JudgeResult(score=0.5, verdict="review", reasoning=str(content)[:500])
        except Exception as exc:
            return JudgeResult(score=0.0, verdict="error", reasoning=str(exc))
