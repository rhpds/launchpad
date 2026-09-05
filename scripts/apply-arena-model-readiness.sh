#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:?KUBECONFIG must point to the Arena credential}"

case "$KUBECONFIG" in
  *config-arena*) ;;
  *)
    echo "refusing to mutate a non-Arena cluster" >&2
    exit 2
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
patch_file="$repo_root/deploy/launchpad/overlays/arena/operational-patches/ovms-granite-2b-readiness.yaml"

oc -n fleet-llm-d patch deployment ovms-granite-2b \
  --type=strategic \
  --patch-file "$patch_file"
oc -n fleet-llm-d rollout status deployment/ovms-granite-2b --timeout=300s
