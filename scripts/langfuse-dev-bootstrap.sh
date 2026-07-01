#!/usr/bin/env bash
# Bootstrap Langfuse dev stack: write .env with headless init keys and start compose.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LF_DIR="$ROOT/deploy/langfuse"
ENV_FILE="$LF_DIR/.env"

mkdir -p "$LF_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  cat >"$ENV_FILE" <<'EOF'
NEXTAUTH_URL=http://localhost:3001
NEXTAUTH_SECRET=changeme-nextauth-secret-dev
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
SALT=changeme-salt-dev
ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000000
LANGFUSE_INIT_ORG_ID=org-egregore-dev
LANGFUSE_INIT_ORG_NAME=Egregore Dev
LANGFUSE_INIT_PROJECT_ID=proj-egregore-dev
LANGFUSE_INIT_PROJECT_NAME=egregore-dev
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-dev-public
LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-dev-secret
LANGFUSE_INIT_USER_EMAIL=dev@egregore.local
LANGFUSE_INIT_USER_NAME=Dev User
LANGFUSE_INIT_USER_PASSWORD=egregore-dev
EOF
  echo "[langfuse-bootstrap] created $ENV_FILE"
else
  echo "[langfuse-bootstrap] using existing $ENV_FILE"
fi

docker compose -f "$LF_DIR/docker-compose.yml" up -d

echo "[langfuse-bootstrap] waiting for Langfuse UI..."
for _ in $(seq 1 60); do
  if curl -sf -m 3 http://localhost:3001/api/public/health >/dev/null 2>&1; then
    echo "[langfuse-bootstrap] Langfuse ready at http://localhost:3001"
    echo "  LANGFUSE_PUBLIC_KEY=pk-lf-dev-public"
    echo "  LANGFUSE_SECRET_KEY=sk-lf-dev-secret"
    echo "  LANGFUSE_HOST=http://localhost:3001"
    exit 0
  fi
  sleep 2
done

echo "[langfuse-bootstrap] WARN: Langfuse did not become healthy in time" >&2
exit 1
