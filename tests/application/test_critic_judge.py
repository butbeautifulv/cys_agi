from __future__ import annotations

import pytest

from cys_core.application.use_cases.process_finding_critic import ProcessFindingCritic
from cys_core.domain.observability.models import JudgeRequest, JudgeResult
from cys_core.domain.security.guardrails import OutputGuardrails


class _Store:
    def __init__(self) -> None:
        self.critic: dict | None = None

    def record_finding(self, envelope): ...
    def record_critic(self, feedback): self.critic = feedback
    def record_awaiting_approval(self, record): ...
    def record_escalation(self, record): ...


class _Judge:
    def judge(self, request: JudgeRequest) -> JudgeResult:
        return JudgeResult(score=0.2, verdict="fail", reasoning="mock")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_critic_rule_path_without_judge():
    store = _Store()
    async def _noop(*_a, **_k):
        return None

    critic = ProcessFindingCritic(
        guardrails=OutputGuardrails(),
        store=store,
        trust_score_threshold=0.5,
        publish_awaiting_approval=_noop,
        publish_escalation_event=lambda **_: False,
        judge_backend=None,
    )
    out = await critic.execute(
        {"sender": "soc", "payload": {"event_id": "e1", "data": {"confidence": 0.9}}}
    )
    assert out["approved"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_critic_uses_judge_backend_when_provided():
    store = _Store()

    async def _noop(*_a, **_k):
        return None

    critic = ProcessFindingCritic(
        guardrails=OutputGuardrails(),
        store=store,
        trust_score_threshold=0.5,
        publish_awaiting_approval=_noop,
        publish_escalation_event=lambda **_: False,
        judge_backend=_Judge(),
    )
    out = await critic.execute(
        {"sender": "soc", "payload": {"event_id": "e1", "data": {"confidence": 0.9}}}
    )
    assert out["approved"] is False
    assert "llm_judge_low_score" in out["issues_detected"]
