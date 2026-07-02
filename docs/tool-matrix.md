# Tool inventory — personas vs implementation

| Tool | Personas | Status | Backend |
|------|----------|--------|---------|
| `playbook_*`, `ti_*` | soc, network, dfir, compliance | wired | veil-mcp |
| `enrich_ioc` | soc, dfir | partial | veil `ti_search_in_category` or stub |
| `web_search` | research, gaia_solver, conductor | wired | enhancer + judge + serper/ddg fallback |
| `search_archived_webpage` | research, gaia_solver | wired | Wayback available API |
| `vision_analyze` | research, dfir | partial | reasoning/vision model when available |
| `python_sandbox` | coding, gaia_solver | wired | local subprocess; HITL-gated |
| `delegate_research` | conductor | wired | in-process research persona |
| `read_document` | research, gaia_solver, dfir | wired | local filesystem reader |
| `reasoning_check` | conductor, gaia_solver | wired | trace critic use case |
| `reasoning_step` | soc, network, intel, hunter, conductor | wired | SGR mandatory reasoning before action |
| `extract_structured_output` | conductor, gaia_solver | wired | LLM extraction tool |
| `run_active_scan` | pentest personas | partial | veneno-mcp when `VENENO_MCP_ENABLED` |
| `query_siem_readonly` | soc | wired | ToolBackend / gateway |
| `rag_query` | soc, consultant, research | wired | ToolBackend / gateway |
| `parse_netflow` | network, dfir | stub | local heuristic |
| `parse_sast_report` | appsec | stub | JSON parse only |
| `read_repo_metadata` | appsec | stub | static JSON |
| `dedup_alerts`, `build_timeline` | soc | stub | static JSON |
| `check_control`, `map_framework` | compliance | stub | static JSON |

Update when wiring real backends in `cys_core/registry/tools.py`.
