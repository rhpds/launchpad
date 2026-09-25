#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kubeconfig="${FLIGHTPATH_KUBECONFIG:-$script_dir/../../.flightpath-admin.kubeconfig}"
namespace="launchpad-flightpath-candidate"
public_origin="https://labs.smg-helix.ai"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$kubeconfig" ]] || fail "Flightpath kubeconfig not found: $kubeconfig"
export KUBECONFIG="$kubeconfig"

infrastructure="$(oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}')"
[[ "$infrastructure" == flightpath-* ]] || fail "Refusing non-Flightpath cluster: $infrastructure"

for secret in tunnel-token launchpad-public-access; do
  oc -n "$namespace" get secret "$secret" >/dev/null \
    || fail "Missing required out-of-Git secret: $namespace/$secret"
done

oc -n "$namespace" create configmap tunnel-router \
  --from-file=router.py="$script_dir/router.py" \
  --dry-run=client -o yaml \
  | oc apply -f - >/dev/null
oc apply -f "$script_dir/flightpath-deployment.yaml" >/dev/null
oc -n "$namespace" rollout status deployment/cloudflare-tunnel --timeout=5m

containers="$(oc -n "$namespace" get deployment cloudflare-tunnel \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n"}{end}')"
grep -qx router <<<"$containers" || fail "router sidecar is absent"
grep -qx cloudflared <<<"$containers" || fail "cloudflared connector is absent"

curl -fsS --retry 10 --retry-all-errors --retry-delay 2 \
  "$public_origin/health" >/dev/null
echo "Flightpath public tunnel router is healthy at $public_origin"
