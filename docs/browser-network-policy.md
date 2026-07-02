# Browser sandbox network policy

When `BROWSER_ENABLED=true`, restrict egress for the browser tool:

| Env | Purpose |
|-----|---------|
| `BROWSER_ENABLED` | Master switch (default `false`) |
| `BROWSER_EGRESS_ALLOWLIST` | Comma-separated host suffixes, e.g. `wikipedia.org,archive.org` |

In Kubernetes, pair with a `NetworkPolicy` denying egress except DNS + allowlisted CIDRs for the worker namespace.

HITL: `browser_use` is classified `HIGH` risk — requires human approval in production (`SecurityMiddleware` interrupt).
