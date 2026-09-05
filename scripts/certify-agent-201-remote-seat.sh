#!/usr/bin/env bash
set -euo pipefail

namespace="${1:?usage: certify-agent-201-remote-seat.sh <namespace> <cluster-id>}"
expected_cluster="${2:?usage: certify-agent-201-remote-seat.sh <namespace> <cluster-id>}"
: "${KUBECONFIG:?KUBECONFIG must point to the expected execution cluster credential}"

actual_cluster="$(
  oc get namespace "$namespace" \
    -o jsonpath='{.metadata.labels.launchpad\.redhat\.com/cluster-id}'
)"
if [[ "$actual_cluster" != "$expected_cluster" ]]; then
  echo "refusing to mutate cluster '${actual_cluster}'; expected '${expected_cluster}'" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host="$(oc get route showroom -n "$namespace" -o jsonpath='{.spec.host}')"
curl_options=(-fsSk)
if [[ -n "${LAUNCHPAD_CURL_INTERFACE:-}" ]]; then
  curl_options+=(--interface "$LAUNCHPAD_CURL_INTERFACE")
fi
if [[ -n "${LAUNCHPAD_INGRESS_IP:-}" ]]; then
  curl_options+=(--resolve "${host}:443:${LAUNCHPAD_INGRESS_IP}")
fi
page="$(curl "${curl_options[@]}" "https://${host}/www/modules/02-deploy-tools.html")"
endpoint="$(printf '%s' "$page" | sed -n "s/.*--from-literal=api-base='\([^']*\)'.*/\1/p" | head -1)"
model="$(printf '%s' "$page" | sed -n "s/.*ADVISOR_MODEL='\([^']*\)'.*/\1/p" | head -1)"

if [[ -z "$endpoint" || -z "$model" ]]; then
  echo "Showroom did not render the required model connection values" >&2
  exit 3
fi

oc create configmap racmaas-connection \
  --from-literal="api-base=${endpoint}" \
  --dry-run=client -o yaml \
  | oc exec -i -n "$namespace" deploy/showroom -c terminal -- \
      oc apply -n "$namespace" -f - >/dev/null

# Keep the short-lived model credential inside the participant terminal. The
# driver verifies only that it exists and never copies it through local stdout.
oc exec -n "$namespace" deploy/showroom -c terminal -- bash -lc '
  test -n "$MAAS_API_KEY"
  oc create secret generic litellm-api-key \
    --from-literal=api-key="$MAAS_API_KEY" \
    --dry-run=client -o yaml | oc apply -f - >/dev/null
'

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
  --containers=solution-agent \
  "ADVISOR_MODEL=${model}" >/dev/null

for deployment in solution-agent solution-ui; do
  oc exec -n "$namespace" deploy/showroom -c terminal -- \
    oc rollout status -n "$namespace" "deployment/${deployment}" \
      --timeout=300s >/dev/null
done

printf '%s\t%s\tdeployed\n' "$namespace" "$expected_cluster"
