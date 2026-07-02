from __future__ import annotations

from cys_core.domain.catalog.models import ModePolicyPayload
from cys_core.domain.policy.defaults import (
    DEFAULT_MODE_POLICY,
    PLAN_BLOCKED_TOOLS,
    READ_ONLY_TOOLS,
    MUTATING_TOOLS,
)
from cys_core.domain.policy.pure import allow_tool_pure, mode_sets_from_policy
from cys_core.domain.runs.models import InteractionMode

_SPAWN_BUS_TYPES = frozenset({"spawn_worker"})


def _mode_sets(profile_id: str | None) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    if profile_id:
        try:
            from cys_core.infrastructure.catalog.profile_policy import get_profile_policy

            return mode_sets_from_policy(get_profile_policy(profile_id).mode_policy)
        except Exception:
            pass
    return mode_sets_from_policy(DEFAULT_MODE_POLICY)


class ModePolicy:
    """Pure domain policy for interaction modes."""

    @staticmethod
    def allow_tool(
        mode: InteractionMode | None,
        tool_name: str,
        profile_id: str | None = None,
        *,
        mode_policy: ModePolicyPayload | None = None,
    ) -> bool:
        if mode_policy is not None:
            return allow_tool_pure(mode, tool_name, mode_policy=mode_policy)
        if profile_id:
            try:
                from cys_core.infrastructure.catalog.profile_policy import get_profile_policy

                return allow_tool_pure(mode, tool_name, mode_policy=get_profile_policy(profile_id).mode_policy)
            except Exception:
                pass
        return allow_tool_pure(mode, tool_name, mode_policy=DEFAULT_MODE_POLICY)

    @staticmethod
    def allow_bus_message(mode: InteractionMode | None, message_type: str) -> bool:
        if mode is None:
            return True
        if mode in (InteractionMode.PLAN, InteractionMode.ASK):
            return message_type not in _SPAWN_BUS_TYPES
        return True

    @staticmethod
    def allow_spawn(mode: InteractionMode | None) -> bool:
        if mode is None:
            return True
        return mode in (InteractionMode.AGENT, InteractionMode.DEBUG)


def _is_mutating(tool_name: str, mutating: frozenset[str] | None = None) -> bool:
    tools = mutating or MUTATING_TOOLS
    if tool_name in tools:
        return True
    prefixes = ("run_", "write_", "spawn_", "execute_")
    return any(tool_name.startswith(prefix) for prefix in prefixes)
