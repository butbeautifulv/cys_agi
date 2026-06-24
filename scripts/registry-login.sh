#!/usr/bin/env bash
# Docker login for GitLab or external registry (Nexus, Harbor, Artifactory).
set -euo pipefail

backend="${REGISTRY_BACKEND:-gitlab}"

# shellcheck source=/dev/null
source "$(dirname "$0")/registry-resolve-env.sh" >/dev/null

login_host=""
login_user=""
login_password=""

case "$backend" in
  gitlab)
    login_host="${CI_REGISTRY:-}"
    login_user="${CI_REGISTRY_USER:-}"
    login_password="${CI_REGISTRY_PASSWORD:-}"
    if [[ -z "$login_host" || -z "$login_user" || -z "$login_password" ]]; then
      echo "ERROR: CI_REGISTRY, CI_REGISTRY_USER, CI_REGISTRY_PASSWORD required for gitlab backend" >&2
      exit 1
    fi
    ;;
  nexus|harbor|artifactory|generic)
    login_host="${REGISTRY_HOST:-}"
    login_user="${REGISTRY_USER:-}"
    login_password="${REGISTRY_PASSWORD:-}"
    if [[ -z "$login_host" || -z "$login_user" || -z "$login_password" ]]; then
      echo "ERROR: REGISTRY_HOST, REGISTRY_USER, REGISTRY_PASSWORD required for backend=$backend" >&2
      exit 1
    fi
    ;;
  *)
    echo "ERROR: unknown REGISTRY_BACKEND=$backend" >&2
    exit 1
    ;;
esac

echo "Logging in to registry (backend=$backend, host=$login_host)"
echo "$login_password" | docker login -u "$login_user" --password-stdin "$login_host"
