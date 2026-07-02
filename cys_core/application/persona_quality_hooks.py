from __future__ import annotations

from collections.abc import Callable

from cys_core.application.use_cases.update_persona_quality import UpdatePersonaQuality
from cys_core.domain.catalog.quality_events import PersonaQualityEvent, PersonaQualityEventKind
from cys_core.domain.catalog.profile_id import DEFAULT_PROFILE_ID
from cys_core.infrastructure.catalog.hybrid_registry import get_agent_catalog
from cys_core.infrastructure.catalog.profile_runtime import get_profile_runtime


def emit_persona_quality(event: PersonaQualityEvent) -> None:
    UpdatePersonaQuality(get_agent_catalog()).apply(event)


def _trust_signal(kind: PersonaQualityEventKind, *, profile_id: str) -> float:
    signals = get_profile_runtime(profile_id).policy.quality_signals
    mapping = {
        PersonaQualityEventKind.JOB_COMPLETED: signals.job_success,
        PersonaQualityEventKind.JOB_FAILED: signals.job_failure,
        PersonaQualityEventKind.TRACE_CRITIC_PASS: signals.trace_critic_pass,
        PersonaQualityEventKind.TRACE_CRITIC_FAIL: signals.trace_critic_fail,
        PersonaQualityEventKind.HITL_PAUSE: signals.hitl_pause,
        PersonaQualityEventKind.BUS_FAILURE: signals.bus_failure,
        PersonaQualityEventKind.CRITIC_PASS: 0.8,
        PersonaQualityEventKind.CRITIC_FAIL: 0.4,
    }
    return mapping.get(kind, 0.5)


def record_event(
    kind: PersonaQualityEventKind,
    persona: str,
    *,
    profile_id: str = DEFAULT_PROFILE_ID,
    trust_signal: float | None = None,
    cost_usd: float = 0.0,
) -> None:
    emit_persona_quality(
        PersonaQualityEvent(
            persona=persona,
            profile_id=profile_id,
            kind=kind,
            trust_signal=trust_signal if trust_signal is not None else _trust_signal(kind, profile_id=profile_id),
            cost_usd=cost_usd,
        )
    )


def record_job_completed(persona: str, *, success: bool, cost_usd: float = 0.0, profile_id: str = DEFAULT_PROFILE_ID) -> None:
    kind = PersonaQualityEventKind.JOB_COMPLETED if success else PersonaQualityEventKind.JOB_FAILED
    record_event(kind, persona, profile_id=profile_id, cost_usd=cost_usd)


def record_critic_verdict(
    persona: str, *, passed: bool, trust_score: float = 0.5, profile_id: str = DEFAULT_PROFILE_ID
) -> None:
    kind = PersonaQualityEventKind.CRITIC_PASS if passed else PersonaQualityEventKind.CRITIC_FAIL
    record_event(
        kind,
        persona,
        profile_id=profile_id,
        trust_signal=trust_score if passed else max(0.1, trust_score * 0.5),
    )


def record_trace_critic(persona: str, *, passed: bool, profile_id: str = DEFAULT_PROFILE_ID) -> None:
    kind = PersonaQualityEventKind.TRACE_CRITIC_PASS if passed else PersonaQualityEventKind.TRACE_CRITIC_FAIL
    record_event(kind, persona, profile_id=profile_id)


def record_hitl_pause(persona: str, *, profile_id: str = DEFAULT_PROFILE_ID) -> None:
    record_event(PersonaQualityEventKind.HITL_PAUSE, persona, profile_id=profile_id)


def record_bus_failure(persona: str, *, profile_id: str = DEFAULT_PROFILE_ID) -> None:
    record_event(PersonaQualityEventKind.BUS_FAILURE, persona, profile_id=profile_id)
