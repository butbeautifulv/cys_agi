#!/usr/bin/env bash
# Resolve REGISTRY image prefix from backend + CI variables.
set -euo pipefail

backend="${REGISTRY_BACKEND:-gitlab}"

case "$backend" in
  gitlab)
    if [[ -z "${REGISTRY:-}" ]]; then
      export REGISTRY="${CI_REGISTRY_IMAGE:-}"
    fi
    ;;
  nexus|harbor|artifactory|generic)
    if [[ -z "${REGISTRY:-}" ]]; then
      if [[ -z "${REGISTRY_HOST:-}" || -z "${REGISTRY_REPOSITORY:-}" ]]; then
        echo "ERROR: REGISTRY_HOST and REGISTRY_REPOSITORY required for backend=$backend" >&2
        exit 1
      fi
      host="${REGISTRY_HOST%/}"
      export REGISTRY="${host}/${REGISTRY_REPOSITORY}"
    fi
    ;;
  *)
    echo "ERROR: unknown REGISTRY_BACKEND=$backend (allowed: gitlab, nexus, harbor, artifactory, generic)" >&2
    exit 1
    ;;
esac

if [[ -z "${REGISTRY:-}" ]]; then
  echo "ERROR: REGISTRY is empty after resolve (backend=$backend)" >&2
  return 1 2>/dev/null || exit 1
fi

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "REGISTRY=$REGISTRY"
fi
