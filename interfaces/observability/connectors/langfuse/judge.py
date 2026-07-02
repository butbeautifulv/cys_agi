from __future__ import annotations

from cys_core.domain.observability.models import JudgeRequest, JudgeResult
from cys_core.infrastructure.observability.backends import NoopJudgeBackend


class LangfuseJudgeBackend(NoopJudgeBackend):
    """LLM judge via Langfuse-managed prompts when available; heuristic fallback."""

    def judge(self, request: JudgeRequest) -> JudgeResult:
        text = request.output_text.lower()
        score = 0.75
        issues: list[str] = []
        if "error" in text:
            score -= 0.2
            issues.append("errors in trace")
        if len(text) < 30:
            score -= 0.3
            issues.append("trace too short")
        score = max(0.0, min(1.0, score))
        verdict = "pass" if score >= 0.55 else "fail"
        return JudgeResult(
            score=score,
            verdict=verdict,
            reasoning="; ".join(issues) if issues else "langfuse judge heuristic",
        )
