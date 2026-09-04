#!/usr/bin/env bash
set -euo pipefail

namespace="${1:?usage: certify-agent-201-seat.sh <namespace>}"
: "${KUBECONFIG:?KUBECONFIG must point to the Arena credential}"

case "$KUBECONFIG" in
  *config-arena*) ;;
  *)
    echo "refusing to mutate a non-Arena cluster" >&2
    exit 2
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host="$(oc get route showroom -n "$namespace" -o jsonpath='{.spec.host}')"
curl_options=(-fsSk)
if [[ -n "${ARENA_CURL_INTERFACE:-}" ]]; then
  curl_options+=(--interface "$ARENA_CURL_INTERFACE")
fi
page="$(curl "${curl_options[@]}" "https://${host}/www/modules/03-wire-agent.html")"
endpoint="$(printf '%s' "$page" | sed -n "s/.*--from-literal=api-base='\([^']*\)'.*/\1/p" | head -1)"
api_key="$(printf '%s' "$page" | sed -n "s/.*--from-literal=api-key='\([^']*\)'.*/\1/p" | head -1)"
model="$(printf '%s' "$page" | sed -n "s/.*ADVISOR_MODEL='\([^']*\)'.*/\1/p" | head -1)"

if [[ -z "$endpoint" || -z "$api_key" || -z "$model" ]]; then
  echo "Showroom did not render the required model connection values" >&2
  exit 3
fi

jq -nc \
  --arg endpoint "$endpoint" \
  --arg api_key "$api_key" \
  '{
    apiVersion: "v1",
    kind: "List",
    items: [
      {
        apiVersion: "v1",
        kind: "ConfigMap",
        metadata: {name: "racmaas-connection"},
        data: {"api-base": $endpoint}
      },
      {
        apiVersion: "v1",
        kind: "Secret",
        metadata: {name: "litellm-api-key"},
        type: "Opaque",
        stringData: {"api-key": $api_key}
      }
    ]
  }' \
  | oc exec -i -n "$namespace" deploy/showroom -c terminal -- \
      oc apply -n "$namespace" -f - >/dev/null

for manifest in \
  advisor-prompt-configmap.yaml \
  solution-tools.yaml \
  solution-agent.yaml \
  solution-ui.yaml
do
  oc exec -i -n "$namespace" deploy/showroom -c terminal -- \
    oc apply -n "$namespace" -f - \
    < "$repo_root/content-intel-xeon6-agent-201/manifests/$manifest" >/dev/null
done

oc exec -n "$namespace" deploy/showroom -c terminal -- \
  oc set env -n "$namespace" deployment/solution-agent \
  "ADVISOR_MODEL=${model}" >/dev/null

for deployment in solution-tools solution-agent solution-ui; do
  oc exec -n "$namespace" deploy/showroom -c terminal -- \
    oc rollout status -n "$namespace" "deployment/${deployment}" \
      --timeout=180s >/dev/null
done

printf '%s\tdeployed\n' "$namespace"
