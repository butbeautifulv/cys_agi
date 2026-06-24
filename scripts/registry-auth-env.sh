#!/usr/bin/env bash
# Export registry credentials for Trivy/cosign image pull auth (source from CI before_script).
set -euo pipefail

backend="${REGISTRY_BACKEND:-gitlab}"

case "$backend" in
  gitlab)
    export TRIVY_USERNAME="${CI_REGISTRY_USER:-}"
    export TRIVY_PASSWORD="${CI_REGISTRY_PASSWORD:-}"
    export REGISTRY_USERNAME="${CI_REGISTRY_USER:-}"
    export REGISTRY_PASSWORD="${CI_REGISTRY_PASSWORD:-}"
    ;;
  nexus|harbor|artifactory|generic)
    export TRIVY_USERNAME="${REGISTRY_USER:-}"
    export TRIVY_PASSWORD="${REGISTRY_PASSWORD:-}"
    export REGISTRY_USERNAME="${REGISTRY_USER:-}"
    export REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-}"
    ;;
  *)
    echo "ERROR: unknown REGISTRY_BACKEND=$backend" >&2
    return 1 2>/dev/null || exit 1
    ;;
esac

if [[ -z "${TRIVY_USERNAME:-}" || -z "${TRIVY_PASSWORD:-}" ]]; then
  echo "ERROR: registry credentials not set for backend=$backend" >&2
  return 1 2>/dev/null || exit 1
fi
