#!/usr/bin/env bash
set -euo pipefail

# Compatibility entry point. The tunnel now runs inside Arena; no laptop port
# forwards or global kube-context changes are used.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export ARENA_KUBECONFIG="${ARENA_KUBECONFIG:-/Users/jkershaw/.kube/config-arena}"
export KUBECONFIG="$ARENA_KUBECONFIG"

exec "$SCRIPT_DIR/../deploy/tunnel-oncluster/apply.sh" "$@"
