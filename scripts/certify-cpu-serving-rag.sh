#!/usr/bin/env bash
set -euo pipefail

namespace="${1:?usage: certify-cpu-serving-rag.sh <namespace>}"
: "${KUBECONFIG:?KUBECONFIG must point to the Arena credential}"

case "$KUBECONFIG" in
  *config-arena*) ;;
  *)
    echo "refusing to validate a non-Arena cluster" >&2
    exit 2
    ;;
esac

host="$(oc get route rag -n "$namespace" -o jsonpath='{.spec.host}')"
base_url="https://${host}"
api_token="$({
  curl -fsSk \
    -H 'Content-Type: application/json' \
    -X POST "${base_url}/api/system/generate-api-key" \
    --data '{"name":"launchpad-rag-certification"}'
} | jq -r '.apiKey.secret')"

if [[ -z "$api_token" || "$api_token" == "null" ]]; then
  echo "AnythingLLM did not issue a certification API token" >&2
  exit 3
fi

auth_ok="$(curl -fsSk -H "Authorization: Bearer ${api_token}" \
  "${base_url}/api/v1/auth" | jq -r '.authenticated')"
[[ "$auth_ok" == "true" ]]

curl -fsSk \
  -H "Authorization: Bearer ${api_token}" \
  -H 'Content-Type: application/json' \
  -X POST "${base_url}/api/v1/workspace/new" \
  --data '{"name":"HR Assistant","chatMode":"query","openAiTemp":0,"openAiHistory":10,"topN":4}' \
  | jq -e '.workspace.slug == "hr-assistant"' >/dev/null

curl -fsSk \
  -H "Authorization: Bearer ${api_token}" \
  -H 'Content-Type: application/json' \
  -X POST "${base_url}/api/v1/document/raw-text" \
  --data '{"textContent":"Launchpad Orion Leave Policy. Every employee receives exactly 17 days of Orion leave per calendar year. This policy fact is unique to this certification document.","addToWorkspaces":"hr-assistant","metadata":{"title":"orion-leave-policy.txt","docSource":"launchpad-certification"}}' \
  | jq -e '.success == true and .documents[0].title == "orion-leave-policy.txt"' \
  >/dev/null

result="$(curl -fsSk \
  -w $'\n%{http_code}\t%{time_total}\n' \
  -H "Authorization: Bearer ${api_token}" \
  -H 'Content-Type: application/json' \
  -X POST "${base_url}/api/v1/workspace/hr-assistant/chat" \
  --data '{"message":"According to the supplied policy, exactly how many days of Orion leave does every employee receive per calendar year?","mode":"query"}')"
response="$(printf '%s\n' "$result" | head -1)"
metadata="$(printf '%s\n' "$result" | tail -1)"

printf '%s' "$response" | jq -e '
  .type == "textResponse"
  and (.textResponse | contains("17"))
  and any(.sources[]?; .title == "orion-leave-policy.txt")
  and (.error == null)
' >/dev/null

printf '%s\t%s\tgrounded=true\n' "$namespace" "$metadata"
