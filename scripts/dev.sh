#!/usr/bin/env bash
# Start egregore dev stack: API + workers + UI (no Langfuse by default).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MPDIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc}"
mkdir -p "$MPDIR"
export PROMETHEUS_MULTIPROC_DIR="$MPDIR"

REPLICAS="${WORKER_REPLICAS:-2}"
IDLE="${WORKER_IDLE_TIMEOUT:-0}"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

echo "[dev] starting API on :8080"
PROMETHEUS_MULTIPROC_DIR="$MPDIR" uv run egregore serve --port 8080 &
PIDS+=($!)

for i in $(seq 1 "$REPLICAS"); do
  echo "[dev] starting worker $i/$REPLICAS"
  PROMETHEUS_MULTIPROC_DIR="$MPDIR" uv run egregore worker --daemon --idle-timeout "$IDLE" &
  PIDS+=($!)
done

echo "[dev] starting UI on :3000"
(cd ui && npm run dev) &
PIDS+=($!)

echo "[dev] API http://localhost:8080  UI http://localhost:3000  (Ctrl+C to stop)"
wait
