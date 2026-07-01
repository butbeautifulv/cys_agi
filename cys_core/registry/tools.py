from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from cys_core.application.ports.tool_backend import ToolBackend

_tool_backend: ToolBackend | None = None


def configure_tool_backend(backend: ToolBackend) -> None:
    global _tool_backend
    _tool_backend = backend


@tool
def read_repo_metadata(repo_path: str) -> str:
    """Read repository metadata (languages, branches, recent commits). Stub for authorized scope."""
    return json.dumps(
        {
            "repo_path": repo_path,
            "languages": ["python", "yaml"],
            "default_branch": "main",
            "ci": "github_actions",
        },
        ensure_ascii=False,
    )


@tool
def parse_sast_report(report_json: str) -> str:
    """Parse SAST report JSON and extract high-signal findings."""
    try:
        data = json.loads(report_json) if report_json.strip().startswith("{") else {"raw": report_json}
    except json.JSONDecodeError:
        data = {"raw": report_json[:2000]}
    return json.dumps({"parsed_findings": data, "count": len(str(data))}, ensure_ascii=False)


@tool
def analyze_workflow(workflow_yaml: str) -> str:
    """Analyze CI/CD workflow for risky patterns (pull_request_target, secrets in env)."""
    risks = []
    lower = workflow_yaml.lower()
    if "pull_request_target" in lower:
        risks.append("pull_request_target usage detected")
    if "aws_access_key" in lower or "secret" in lower:
        risks.append("secrets referenced in workflow environment")
    return json.dumps({"risks": risks or ["no obvious workflow risks in stub"]}, ensure_ascii=False)


@tool
def run_active_scan(target: str) -> str:
    """Run active security scan on authorized target. Requires HITL approval."""
    from cys_core.integrations.veneno_mcp_client import call_veneno_mcp_tool, veneno_mcp_enabled

    if veneno_mcp_enabled():
        result = call_veneno_mcp_tool("run_active_scan", {"target": target})
        return json.dumps(result, ensure_ascii=False)
    return json.dumps(
        {"status": "simulated", "target": target, "note": "PoC analysis only; enable VENENO_MCP_ENABLED for execution"},
        ensure_ascii=False,
    )


@tool
def parse_netflow(netflow_text: str) -> str:
    """Parse NetFlow summary text into structured indicators."""
    return json.dumps(
        {
            "source": "netflow_stub",
            "indicators": ["periodic_tls", "non_browser_traffic"] if "90s" in netflow_text else [],
            "raw_excerpt": netflow_text[:500],
        },
        ensure_ascii=False,
    )


@tool
def enrich_ioc(ioc: str) -> str:
    """Enrich IP/domain IOC via Veil threat-intel when available."""
    from cys_core.integrations.veil_mcp_client import call_veil_mcp_tool, veil_mcp_enabled

    if veil_mcp_enabled():
        result = call_veil_mcp_tool("ti_search_in_category", {"query": ioc, "category": "ioc", "limit": 5})
        if result.get("success"):
            return json.dumps({"ioc": ioc, "source": "veil-ti", "enrichment": result.get("result")}, ensure_ascii=False)
    return json.dumps({"ioc": ioc, "reputation": "suspicious", "tags": ["stub"], "source": "stub"}, ensure_ascii=False)


@tool
def correlate_dns(dns_events: str) -> str:
    """Correlate DNS events for beaconing patterns."""
    return json.dumps({"pattern": "periodic_lookup", "confidence": 0.7}, ensure_ascii=False)


@tool
def query_siem_readonly(query: str, time_range: str = "24h") -> str:
    """Execute read-only SIEM search. Worker runs route via MCP Tool Gateway."""
    if _tool_backend is None:
        return json.dumps({"error": "tool backend not configured"}, ensure_ascii=False)
    return json.dumps(
        _tool_backend.query_siem(query=query, time_range=time_range),
        ensure_ascii=False,
    )


@tool
def rag_query(query: str, persona: str = "soc", tenant: str = "default") -> str:
    """Retrieve ACL-filtered knowledge base chunks via MCP Tool Gateway."""
    if _tool_backend is None:
        return json.dumps({"error": "tool backend not configured"}, ensure_ascii=False)
    return json.dumps(
        _tool_backend.rag_query(query=query, persona=persona, tenant=tenant),
        ensure_ascii=False,
    )


@tool
def dedup_alerts(alerts_text: str) -> str:
    """Deduplicate and cluster SIEM alerts."""
    return json.dumps({"deduplicated_count": 1, "clusters": ["powershell_encoded"]}, ensure_ascii=False)


@tool
def build_timeline(events_text: str) -> str:
    """Build incident timeline from correlated events."""
    return json.dumps(
        {"timeline": ["T+0 EDR alert", "T+2m proxy anomaly", "T+10m dedup repeat"]},
        ensure_ascii=False,
    )


@tool
def correlate_findings(findings_json: str) -> str:
    """Correlate findings across telemetry sources."""
    return json.dumps({"correlated": True, "priority": "P2"}, ensure_ascii=False)


@tool
def check_control(framework: str, control_id: str, evidence: str) -> str:
    """Check compliance control against provided evidence."""
    return json.dumps(
        {
            "framework": framework,
            "control_id": control_id,
            "status": "partial",
            "gaps": ["missing quarterly access review"] if "60%" in evidence else [],
        },
        ensure_ascii=False,
    )


@tool
def map_framework(observation: str) -> str:
    """Map observation to compliance framework controls."""
    return json.dumps({"framework": "SOC2", "controls": ["CC6.1", "CC7.2"]}, ensure_ascii=False)


@tool
def audit_evidence(evidence_text: str) -> str:
    """Audit evidence retention and auditability."""
    return json.dumps({"auditability": "partial", "ticket_coverage": "60%"}, ensure_ascii=False)


@tool
def execute_command(command: str) -> str:
    """Execute shell command. RESTRICTED — should be denied for most agents."""
    return json.dumps({"executed": command, "status": "denied_by_policy"}, ensure_ascii=False)


@tool
def search_personas(query: str) -> str:
    """Search registered agent personas by keyword."""
    from cys_core.registry.discovery_tools import search_personas as _search

    return json.dumps(_search(query), ensure_ascii=False)


@tool
def search_skills(query: str) -> str:
    """Search product skills by keyword."""
    from cys_core.registry.discovery_tools import search_skills as _search

    return json.dumps(_search(query), ensure_ascii=False)


@tool
def search_tools(query: str, mode: str = "agent") -> str:
    """Search available tools filtered by interaction mode policy."""
    from cys_core.domain.runs.models import InteractionMode
    from cys_core.registry.discovery_tools import search_tools as _search

    try:
        interaction_mode = InteractionMode(mode)
    except ValueError:
        interaction_mode = InteractionMode.AGENT
    return json.dumps(_search(query, mode=interaction_mode), ensure_ascii=False)


@tool
def ask_user(question: str, *, context_id: str = "", tenant_id: str = "default") -> str:
    """Pause run and surface a clarifying question to the operator."""
    return json.dumps(
        {
            "status": "awaiting_user",
            "question": question,
            "context_id": context_id,
            "tenant_id": tenant_id,
        },
        ensure_ascii=False,
    )


@tool
def update_todos(todos_json: str, *, context_id: str = "", tenant_id: str = "default") -> str:
    """Replace work todos for the active run context."""
    from cys_core.domain.runs.plan_models import WorkTodo
    from cys_core.infrastructure.runs.todo_store import InMemoryWorkTodoStore

    try:
        raw = json.loads(todos_json) if todos_json.strip().startswith("[") else []
    except json.JSONDecodeError:
        raw = []
    todos = [WorkTodo.model_validate(item) for item in raw]
    store = InMemoryWorkTodoStore()
    if context_id:
        store.replace_todos(tenant_id, context_id, todos)
    return json.dumps({"updated": len(todos), "context_id": context_id}, ensure_ascii=False)


_ALL_TOOLS: list[BaseTool] = [
    read_repo_metadata,
    parse_sast_report,
    analyze_workflow,
    run_active_scan,
    parse_netflow,
    enrich_ioc,
    correlate_dns,
    query_siem_readonly,
    rag_query,
    dedup_alerts,
    build_timeline,
    correlate_findings,
    check_control,
    map_framework,
    audit_evidence,
    execute_command,
    search_personas,
    search_skills,
    search_tools,
    ask_user,
    update_todos,
]

from cys_core.registry.veil_tools import build_veil_tools

_ALL_TOOLS.extend(build_veil_tools())


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {t.name: t for t in _ALL_TOOLS}

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def resolve(self, names: list[str]) -> list[BaseTool]:
        return [self.get(n) for n in names]

    def names(self) -> list[str]:
        return list(self._tools.keys())


tool_registry = ToolRegistry()
