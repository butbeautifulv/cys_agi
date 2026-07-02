from __future__ import annotations

from cys_core.domain.catalog.models import ModePolicyPayload, ProfilePolicyPayload
from cys_core.domain.catalog.profile_id import DEFAULT_PROFILE_ID
from cys_core.domain.reasoning.sgr_models import SgrPolicy
from cys_core.domain.workers.models import PersonaBudget

DEFAULT_BUS_POLICY: dict[str, list[str]] = {
    "critic": ["control"],
    "worker": ["critic", "control"],
}

ESCALATION_ONLY_PATHS: set[tuple[str, str]] = {
    ("soc", "redteam"),
    ("network", "redteam"),
    ("intel", "redteam"),
    ("hunter", "redteam"),
}

MUTATING_TOOLS = frozenset({"spawn_worker", "update_todos"})

READ_ONLY_TOOLS = frozenset(
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
        "web_search",
        "read_document",
        "reasoning_check",
        "reasoning_step",
        "vision_analyze",
        "search_archived_webpage",
    }
)

PLAN_BLOCKED_TOOLS = MUTATING_TOOLS | frozenset(
    {
        "ask_user",
        "delegate_research",
        "python_sandbox",
        "browser_use",
        "plan_tool_calls",
    }
)

DEFAULT_MODE_POLICY = ModePolicyPayload(
    read_only_tools=sorted(READ_ONLY_TOOLS),
    plan_blocked_tools=sorted(PLAN_BLOCKED_TOOLS),
    mutating_tools=sorted(MUTATING_TOOLS),
)

ACTION_RISK_MAPPING: dict[str, str] = {
    "parse_netflow": "low",
    "enrich_ioc": "low",
    "correlate_dns": "low",
    "query_siem_readonly": "low",
    "rag_query": "low",
    "dedup_alerts": "low",
    "build_timeline": "low",
    "correlate_findings": "low",
    "check_control": "low",
    "map_framework": "low",
    "audit_evidence": "low",
    "read_repo_metadata": "low",
    "parse_sast_report": "low",
    "web_search": "low",
    "read_document": "low",
    "search_archived_webpage": "low",
    "vision_analyze": "medium",
    "reasoning_check": "low",
    "reasoning_step": "low",
    "extract_structured_output": "low",
    "search_personas": "low",
    "search_skills": "low",
    "search_tools": "low",
    "ask_user": "low",
    "load_skill": "low",
    "update_todos": "medium",
    "delegate_research": "medium",
    "spawn_worker": "high",
    "plan_tool_calls": "medium",
    "create_report_outline": "low",
    "transcribe_audio": "medium",
    "analyze_workflow": "medium",
    "python_sandbox": "high",
    "browser_use": "high",
    "write_file": "medium",
    "run_active_scan": "high",
    "execute_command": "critical",
    "send_email": "high",
    "database_delete": "critical",
    "transfer_funds": "critical",
}

PROFILE_TOOL_ALLOWLIST: dict[str, frozenset[str] | None] = {
    DEFAULT_PROFILE_ID: None,
    "gaia-bench": frozenset(
        {
            "web_search",
            "read_document",
            "reasoning_check",
            "extract_structured_output",
            "delegate_research",
            "python_sandbox",
            "vision_analyze",
            "search_archived_webpage",
            "plan_tool_calls",
            "browser_use",
            "transcribe_audio",
            "load_skill",
            "search_personas",
            "search_skills",
            "search_tools",
            "update_todos",
            "ask_user",
        }
    ),
    "general": frozenset(
        {
            "search_personas",
            "search_skills",
            "search_tools",
            "update_todos",
            "ask_user",
            "web_search",
            "read_document",
            "reasoning_check",
            "extract_structured_output",
            "delegate_research",
            "load_skill",
            "plan_tool_calls",
            "create_report_outline",
        }
    ),
}

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
    "conductor": PersonaBudget(max_tokens=60_000, max_cost_usd=3.0),
    "gaia_solver": PersonaBudget(max_tokens=80_000, max_cost_usd=4.0),
    "research": PersonaBudget(max_tokens=55_000, max_cost_usd=2.5),
    "coding": PersonaBudget(max_tokens=70_000, max_cost_usd=3.5),
}

PERSONA_CLEARANCE: dict[str, str] = {
    "soc": "confidential",
    "network": "confidential",
    "compliance": "restricted",
    "redteam": "confidential",
    "intel": "confidential",
    "hunter": "confidential",
    "identity": "confidential",
    "dfir": "restricted",
    "cloud": "confidential",
    "purple": "internal",
    "consultant": "internal",
    "coordinator": "restricted",
    "critic": "internal",
}


def default_profile_policy_payload() -> ProfilePolicyPayload:
    tool_allowlist: dict[str, list[str] | None] = {}
    for profile_id, allow in PROFILE_TOOL_ALLOWLIST.items():
        tool_allowlist[profile_id] = None if allow is None else sorted(allow)
    tool_risk = dict(ACTION_RISK_MAPPING)
    escalation_paths = [list(pair) for pair in sorted(ESCALATION_ONLY_PATHS)]
    return ProfilePolicyPayload(
        tool_allowlist=tool_allowlist,
        tool_risk=tool_risk,
        hitl_auto_approve_threshold="low",
        mode_policy=DEFAULT_MODE_POLICY,
        escalation_paths=escalation_paths,
        max_spawn_depth=5,
        cost_per_1k_tokens_usd=0.003,
        delegate_budget_fraction=0.35,
        sgr=SgrPolicy(),
    )


def gaia_profile_policy_payload() -> ProfilePolicyPayload:
    policy = default_profile_policy_payload()
    return policy.model_copy(update={"sgr": SgrPolicy(enabled=True, mode="sgr_hybrid")})
