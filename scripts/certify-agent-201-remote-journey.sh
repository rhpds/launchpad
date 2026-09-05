#!/usr/bin/env bash
set -euo pipefail

namespace="${1:?usage: certify-agent-201-remote-journey.sh <namespace> <cluster-id>}"
expected_cluster="${2:?usage: certify-agent-201-remote-journey.sh <namespace> <cluster-id>}"
: "${KUBECONFIG:?KUBECONFIG must point to the expected execution cluster credential}"

actual_cluster="$(
  oc get namespace "$namespace" \
    -o jsonpath='{.metadata.labels.launchpad\.redhat\.com/cluster-id}'
)"
if [[ "$actual_cluster" != "$expected_cluster" ]]; then
  echo "refusing to validate cluster '${actual_cluster}'; expected '${expected_cluster}'" >&2
  exit 2
fi

tools_host="$(oc get route tools -n "$namespace" -o jsonpath='{.spec.host}')"
agent_host="$(oc get route agent -n "$namespace" -o jsonpath='{.spec.host}')"
app_host="$(oc get route app -n "$namespace" -o jsonpath='{.spec.host}')"
curl_options=(-fsSk)
if [[ -n "${LAUNCHPAD_CURL_INTERFACE:-}" ]]; then
  curl_options+=(--interface "$LAUNCHPAD_CURL_INTERFACE")
fi
tools_curl_options=("${curl_options[@]}")
agent_curl_options=("${curl_options[@]}")
app_curl_options=("${curl_options[@]}")
if [[ -n "${LAUNCHPAD_INGRESS_IP:-}" ]]; then
  tools_curl_options+=(--resolve "${tools_host}:443:${LAUNCHPAD_INGRESS_IP}")
  agent_curl_options+=(--resolve "${agent_host}:443:${LAUNCHPAD_INGRESS_IP}")
  app_curl_options+=(--resolve "${app_host}:443:${LAUNCHPAD_INGRESS_IP}")
fi

[[ "$(curl "${tools_curl_options[@]}" -o /dev/null -w '%{http_code}' "https://${tools_host}/health")" == "200" ]]
[[ "$(curl "${agent_curl_options[@]}" -o /dev/null -w '%{http_code}' "https://${agent_host}/health")" == "200" ]]
[[ "$(curl "${app_curl_options[@]}" -o /dev/null -w '%{http_code}' "https://${app_host}/")" == "200" ]]

curl "${tools_curl_options[@]}" \
  -X POST "https://${tools_host}/mcp" \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}' \
  | jq -e '
      [.result.tools[].name] as $names
      | ($names | length) == 3
      and ($names | contains([
        "intel_hardware_lookup",
        "openshift_capabilities",
        "reference_architectures"
      ]))
    ' >/dev/null

result="$(curl "${agent_curl_options[@]}" \
  -w $'\n%{http_code}\t%{time_total}\n' \
  -X POST "https://${agent_host}/api/v1/advise" \
  -H 'Content-Type: application/json' \
  --data '{"query":"A retail chain needs real-time inventory prediction across 500 stores on an on-premises OpenShift platform. Recommend a sourced Intel and Red Hat architecture with a migration path."}')"
response="$(printf '%s\n' "$result" | head -1)"
metadata="$(printf '%s\n' "$result" | tail -1)"

printf '%s' "$response" | jq -e '
  (.brief | type == "string" and length > 100)
  and (.requirements != null)
  and (.hardware_options != null)
  and (.platform_capabilities != null)
  and (.architecture != null)
  and ([.inference_log[] | select(.error != null)] | length == 0)
  and ([.inference_log[] | select(.tool == "intel_hardware_lookup")] | length >= 1)
  and ([.inference_log[] | select(.tool == "openshift_capabilities")] | length >= 1)
  and ([.inference_log[] | select(.tool == "reference_architectures")] | length >= 1)
' >/dev/null

printf '%s\t%s\t%s\tfunctional-agent=true\n' \
  "$namespace" "$expected_cluster" "$metadata"
