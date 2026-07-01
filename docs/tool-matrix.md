# Tool inventory — personas vs implementation

| Tool | Personas | Status | Backend |
|------|----------|--------|---------|
| `playbook_*`, `ti_*` | soc, network, dfir, compliance | wired | veil-mcp |
| `enrich_ioc` | soc, dfir | partial | veil `ti_search_in_category` or stub |
| `run_active_scan` | pentest personas | partial | veneno-mcp when `VENENO_MCP_ENABLED` |
| `query_siem_readonly` | soc | wired | ToolBackend / gateway |
| `rag_query` | soc, consultant | wired | ToolBackend / gateway |
| `parse_netflow` | network, dfir | stub | local heuristic |
| `parse_sast_report` | appsec | stub | JSON parse only |
| `read_repo_metadata` | appsec | stub | static JSON |
| `dedup_alerts`, `build_timeline` | soc | stub | static JSON |
| `check_control`, `map_framework` | compliance | stub | static JSON |

Update when wiring real backends in `cys_core/registry/tools.py`.
