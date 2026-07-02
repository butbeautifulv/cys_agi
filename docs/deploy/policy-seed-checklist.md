# Policy platform production checklist

After deploying egregore with `USE_DYNAMIC_CATALOG=true`:

1. Run catalog seed: `uv run python scripts/catalog_cli.py seed`
2. Verify profile policy: `GET /catalog/profiles/cybersec-soc/policy`
3. Compare live vs seed defaults: `uv run python scripts/catalog_cli.py policy diff --profile-id cybersec-soc`
4. Confirm tool allowlist blocks bench profiles: check `policy.tool_allowlist.gaia-bench`
5. Confirm MCP veil server lists `allowed_tools` in `mcp_server_catalog`
6. Reload workers after policy PUT: `POST /catalog/reload`
7. Watch Grafana panel **Policy drift** (`cys_catalog_version` per `profile_id`)

Seed sources (review in git, runtime truth in Postgres):

- `bootstrap/policy_defaults.py` — risk map, mode policy, escalation paths
- `agents/personas/*` — persona tools, capabilities, budgets
- `agents/rules/*.md` — copied into `ProfilePack.global_rules` on seed
