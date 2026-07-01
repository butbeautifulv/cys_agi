#!/usr/bin/env bash
# Register LLM-as-judge prompt template in Langfuse (dev).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${LANGFUSE_HOST:-http://localhost:3001}"
PUB="${LANGFUSE_PUBLIC_KEY:-pk-lf-dev-public}"
SEC="${LANGFUSE_SECRET_KEY:-sk-lf-dev-secret}"

if ! curl -sf -m 3 "$HOST/api/public/health" >/dev/null 2>&1; then
  echo "[langfuse-judge] Langfuse not reachable at $HOST — run make langfuse-dev-setup first" >&2
  exit 1
fi

echo "[langfuse-judge] judge prompt 'critic-llm-judge' should be created in Langfuse UI"
echo "  Use template variables: finding_json, persona, severity"
echo "  Set CRITIC_USE_LLM_JUDGE=true in projects/egregore/.env after keys are configured"
exit 0
