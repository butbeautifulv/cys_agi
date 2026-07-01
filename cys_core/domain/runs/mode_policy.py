from __future__ import annotations

from cys_core.domain.runs.models import InteractionMode

_MUTATING_TOOL_PREFIXES = ("run_", "write_", "spawn_", "execute_")
_MUTATING_TOOLS = frozenset({"spawn_worker", "update_todos"})
_READ_ONLY_TOOLS = frozenset(
    {
        "query_siem_readonly",
        "rag_query",
        "playbook_search",
        "playbook_get",
        "playbook_for_technique",
        "playbook_procedure",
        "playbook_framework",
        "ti_search_in_category",
        "search_personas",
        "search_skills",
        "search_tools",
        "read_repo_metadata",
        "parse_sast_report",
        "parse_netflow",
        "enrich_ioc",
        "correlate_dns",
        "dedup_alerts",
        "build_timeline",
        "correlate_findings",
        "load_skill",
    }
)
_SPAWN_BUS_TYPES = frozenset({"spawn_worker"})
_PLAN_BLOCKED_TOOLS = _MUTATING_TOOLS | frozenset({"ask_user"})


class ModePolicy:
    """Pure domain policy for interaction modes."""

    @staticmethod
    def allow_tool(mode: InteractionMode | None, tool_name: str) -> bool:
        if mode is None:
            return True
        if mode == InteractionMode.PLAN:
            return tool_name not in _PLAN_BLOCKED_TOOLS and not _is_mutating(tool_name)
        if mode == InteractionMode.ASK:
            return tool_name in _READ_ONLY_TOOLS or tool_name.startswith("search_")
        return True

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


def _is_mutating(tool_name: str) -> bool:
    if tool_name in _MUTATING_TOOLS:
        return True
    return any(tool_name.startswith(prefix) for prefix in _MUTATING_TOOL_PREFIXES)
