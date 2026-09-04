#!/usr/bin/env bash
set -euo pipefail

# Compatibility helper for reading a Quick Tunnel hostname from a log file.
# It deliberately performs no Kubernetes, Keycloak, OAuth, database, or code
# mutations. Arena configuration is applied by apply.sh using the operator's
# explicitly pinned kubeconfig and the Launchpad admin API.

TUNNEL_LOG="${TUNNEL_LOG:-/shared/cloudflared.log}"

for ((attempt=1; attempt<=90; attempt++)); do
    if [[ -f "$TUNNEL_LOG" ]]; then
        tunnel_host=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1 || true)
        if [[ -n "$tunnel_host" ]]; then
            printf '%s\n' "$tunnel_host"
            exit 0
        fi
    fi
    sleep 2
done

printf 'Quick Tunnel hostname was not available after 180 seconds\n' >&2
exit 1
