#!/usr/bin/env bash
set -euo pipefail

namespace="${1:?usage: certify-tool-calling-journey.sh <namespace>}"
: "${KUBECONFIG:?KUBECONFIG must point to the Arena credential}"

case "$KUBECONFIG" in
  *config-arena*) ;;
  *)
    echo "refusing to validate a non-Arena cluster" >&2
    exit 2
    ;;
esac

host="$(oc get route showroom -n "$namespace" -o jsonpath='{.spec.host}')"
curl_options=(-fsSk)
if [[ -n "${ARENA_CURL_INTERFACE:-}" ]]; then
  curl_options+=(--interface "$ARENA_CURL_INTERFACE")
fi
if [[ -n "${ARENA_INGRESS_IP:-}" ]]; then
  curl_options+=(--resolve "${host}:443:${ARENA_INGRESS_IP}")
fi

page="$(curl "${curl_options[@]}" "https://${host}/www/modules/02-serving-with-tools.html")"
model_url="$(printf '%s' "$page" | sed -n 's/.*export MODEL_URL=\([^< ]*\).*/\1/p' | head -1)"
model="$(printf '%s' "$page" | sed -n 's/.*export MODEL_NAME=\([^< ]*\).*/\1/p' | head -1)"
api_key="$(printf '%s' "$page" | sed -n 's/.*export MODEL_API_KEY=\([^< ]*\).*/\1/p' | head -1)"

if [[ -z "$model_url" || -z "$model" || -z "$api_key" ]]; then
  echo "Showroom did not render the required model connection values" >&2
  exit 3
fi

request="$(jq -nc --arg model "$model" '{
  model:$model,
  messages:[{role:"user",content:"What is the weather in Austin right now?"}],
  tools:[{
    type:"function",
    function:{
      name:"get_weather",
      description:"Get the current weather for a city",
      parameters:{
        type:"object",
        properties:{city:{type:"string"}},
        required:["city"]
      }
    }
  }],
  tool_choice:"auto",
  max_tokens:128,
  temperature:0
}')"

first_result="$({
  printf '%s' "$request" \
    | oc exec -i -n "$namespace" deploy/showroom -c terminal -- \
        curl -fsS -w $'\n%{http_code}\t%{time_total}\n' \
          -H "Authorization: Bearer ${api_key}" \
          -H 'Content-Type: application/json' \
          -X POST "${model_url}/chat/completions" \
          --data-binary @-
})"
first_response="$(printf '%s\n' "$first_result" | head -1)"
first_metadata="$(printf '%s\n' "$first_result" | tail -1)"

printf '%s' "$first_response" | jq -e '
  .choices[0].message.tool_calls[0].function.name == "get_weather"
  and (
    .choices[0].message.tool_calls[0].function.arguments
    | fromjson
    | .city
    | ascii_downcase
    | contains("austin")
  )
' >/dev/null

assistant_message="$(printf '%s' "$first_response" | jq -c '.choices[0].message')"
final_request="$(jq -nc \
  --arg model "$model" \
  --argjson assistant "$assistant_message" \
  '{
    model:$model,
    messages:[
      {role:"user",content:"What is the weather in Austin right now?"},
      $assistant,
      {
        role:"tool",
        tool_call_id:$assistant.tool_calls[0].id,
        content:"{\"temperature\":78,\"unit\":\"fahrenheit\",\"condition\":\"sunny\"}"
      }
    ],
    max_tokens:128,
    temperature:0
  }')"

final_result="$({
  printf '%s' "$final_request" \
    | oc exec -i -n "$namespace" deploy/showroom -c terminal -- \
        curl -fsS -w $'\n%{http_code}\t%{time_total}\n' \
          -H "Authorization: Bearer ${api_key}" \
          -H 'Content-Type: application/json' \
          -X POST "${model_url}/chat/completions" \
          --data-binary @-
})"
final_response="$(printf '%s\n' "$final_result" | head -1)"
final_metadata="$(printf '%s\n' "$final_result" | tail -1)"

printf '%s' "$final_response" | jq -e '
  .choices[0].message.content as $answer
  | ($answer | type == "string")
    and ($answer | test("78"))
    and ($answer | test("sunny"; "i"))
' >/dev/null

first_seconds="$(printf '%s' "$first_metadata" | cut -f2)"
final_seconds="$(printf '%s' "$final_metadata" | cut -f2)"
total_seconds="$(awk -v first="$first_seconds" -v final="$final_seconds" 'BEGIN {printf "%.6f", first + final}')"
printf '%s\t200\t%s\tcomplete-tool-protocol=true\n' "$namespace" "$total_seconds"
