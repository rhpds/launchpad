#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kubeconfig="${FLIGHTPATH_KUBECONFIG:-$repo_root/.flightpath-admin.kubeconfig}"
candidate_namespace="launchpad-flightpath-candidate"
keycloak_namespace="launchpad-stage"
public_origin="https://labs.smg-helix.ai"
keycloak_local="http://127.0.0.1:18087"
keycloak_internal="http://keycloak.launchpad-stage.svc:8080"

fail() { echo "FAIL: $*" >&2; exit 1; }
log() { echo "[flightpath-public] $*"; }

[[ -f "$kubeconfig" ]] || fail "Flightpath kubeconfig not found: $kubeconfig"
export KUBECONFIG="$kubeconfig"
infrastructure="$(oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}')"
[[ "$infrastructure" == flightpath-* ]] || fail "Refusing non-Flightpath cluster: $infrastructure"

for resource in \
  "secret/$candidate_namespace/tunnel-token" \
  "secret/$keycloak_namespace/keycloak-stage-bootstrap" \
  "deployment/$candidate_namespace/backend" \
  "deployment/$candidate_namespace/public-access-gateway" \
  "deployment/$keycloak_namespace/keycloak"; do
  kind="${resource%%/*}"
  remainder="${resource#*/}"
  namespace="${remainder%%/*}"
  name="${remainder#*/}"
  oc -n "$namespace" get "$kind" "$name" >/dev/null \
    || fail "Missing prerequisite $kind/$namespace/$name"
done

pf_log="$(mktemp /tmp/launchpad-flightpath-keycloak.XXXXXX)"
oc -n "$keycloak_namespace" port-forward service/keycloak 18087:8080 >"$pf_log" 2>&1 &
pf_pid=$!
cleanup() { kill "$pf_pid" 2>/dev/null || true; }
trap cleanup EXIT
for attempt in {1..40}; do
  curl -fsS --max-time 2 "$keycloak_local/realms/master/.well-known/openid-configuration" >/dev/null 2>&1 && break
  sleep 0.5
done
kill -0 "$pf_pid" 2>/dev/null || fail "Keycloak port-forward failed; inspect $pf_log"

admin_user="$(oc -n "$keycloak_namespace" get secret keycloak-stage-bootstrap \
  -o jsonpath='{.data.username}' | base64 --decode)"
admin_password="$(oc -n "$keycloak_namespace" get secret keycloak-stage-bootstrap \
  -o jsonpath='{.data.password}' | base64 --decode)"
broker_key="$(oc -n "$keycloak_namespace" get secret keycloak-stage-bootstrap \
  -o jsonpath='{.data.broker-key}' | base64 --decode)"
admin_token="$(curl -fsS "$keycloak_local/realms/master/protocol/openid-connect/token" \
  -d client_id=admin-cli \
  --data-urlencode "username=$admin_user" \
  --data-urlencode "password=$admin_password" \
  -d grant_type=password | jq -r .access_token)"
[[ -n "$admin_token" && "$admin_token" != null ]] || fail "Could not authenticate to Keycloak admin API"
unset admin_password

auth_header="Authorization: Bearer $admin_token"
realm_status="$(curl -sS -o /dev/null -w '%{http_code}' \
  "$keycloak_local/admin/realms/launchpad-public" -H "$auth_header")"
if [[ "$realm_status" == "404" ]]; then
  log "Creating the isolated launchpad-public realm"
  curl -fsS -X POST "$keycloak_local/admin/realms" \
    -H "$auth_header" -H 'Content-Type: application/json' \
    --data "$(jq -nc --arg origin "$public_origin" '{realm:"launchpad-public",enabled:true,sslRequired:"external",attributes:{frontendUrl:$origin}}')" >/dev/null
elif [[ "$realm_status" != "200" ]]; then
  fail "Unexpected Keycloak realm lookup status: $realm_status"
fi

flow_alias="Launchpad public passwordless browser"
flows="$(curl -fsS "$keycloak_local/admin/realms/launchpad-public/authentication/flows" -H "$auth_header")"
if ! jq -e --arg alias "$flow_alias" '.[] | select(.alias == $alias)' <<<"$flows" >/dev/null; then
  log "Creating the order-code browser flow"
  curl -fsS -X POST "$keycloak_local/admin/realms/launchpad-public/authentication/flows" \
    -H "$auth_header" -H 'Content-Type: application/json' \
    --data "$(jq -nc --arg alias "$flow_alias" '{alias:$alias,providerId:"basic-flow",topLevel:true,builtIn:false}')" >/dev/null
fi

flow_url="$keycloak_local/admin/realms/launchpad-public/authentication/flows/$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$flow_alias")/executions"
executions="$(curl -fsS "$flow_url" -H "$auth_header")"
for provider in auth-cookie launchpad-order-code; do
  if ! jq -e --arg provider "$provider" '.[] | select(.providerId == $provider)' <<<"$executions" >/dev/null; then
    curl -fsS -X POST \
      "$flow_url/execution" \
      -H "$auth_header" -H 'Content-Type: application/json' \
      --data "$(jq -nc --arg provider "$provider" '{provider:$provider}')" >/dev/null
  fi
done

executions="$(curl -fsS "$flow_url" -H "$auth_header")"
for provider in auth-cookie launchpad-order-code; do
  execution="$(jq -c --arg provider "$provider" '.[] | select(.providerId == $provider)' <<<"$executions")"
  [[ -n "$execution" ]] || fail "Missing Keycloak execution: $provider"
  curl -fsS -X PUT "$flow_url" \
    -H "$auth_header" -H 'Content-Type: application/json' \
    --data "$(jq -c '.requirement="ALTERNATIVE"' <<<"$execution")" >/dev/null
done

realm="$(curl -fsS "$keycloak_local/admin/realms/launchpad-public" -H "$auth_header")"
realm="$(jq -c --arg origin "$public_origin" --arg flow "$flow_alias" \
  '.browserFlow=$flow | .attributes.frontendUrl=$origin' <<<"$realm")"
curl -fsS -X PUT "$keycloak_local/admin/realms/launchpad-public" \
  -H "$auth_header" -H 'Content-Type: application/json' --data "$realm" >/dev/null

client_id="launchpad-public-gateway"
clients="$(curl -fsS "$keycloak_local/admin/realms/launchpad-public/clients?clientId=$client_id" -H "$auth_header")"
client_uuid="$(jq -r '.[0].id // empty' <<<"$clients")"
if [[ -z "$client_uuid" ]]; then
  log "Creating the public gateway OIDC client"
  client_secret="$(openssl rand -hex 32)"
  curl -fsS -X POST "$keycloak_local/admin/realms/launchpad-public/clients" \
    -H "$auth_header" -H 'Content-Type: application/json' \
    --data "$(jq -nc --arg id "$client_id" --arg secret "$client_secret" --arg origin "$public_origin" \
      '{clientId:$id,enabled:true,protocol:"openid-connect",publicClient:false,secret:$secret,standardFlowEnabled:true,directAccessGrantsEnabled:false,redirectUris:[($origin+"/oauth2/callback")],webOrigins:[$origin]}')" >/dev/null
  clients="$(curl -fsS "$keycloak_local/admin/realms/launchpad-public/clients?clientId=$client_id" -H "$auth_header")"
  client_uuid="$(jq -r '.[0].id // empty' <<<"$clients")"
else
  client="$(jq -c '.[0]' <<<"$clients" | jq -c --arg origin "$public_origin" \
    '.redirectUris=[($origin+"/oauth2/callback")] | .webOrigins=[$origin] | .enabled=true | .standardFlowEnabled=true')"
  curl -fsS -X PUT "$keycloak_local/admin/realms/launchpad-public/clients/$client_uuid" \
    -H "$auth_header" -H 'Content-Type: application/json' --data "$client" >/dev/null
  client_secret="$(curl -fsS "$keycloak_local/admin/realms/launchpad-public/clients/$client_uuid/client-secret" \
    -H "$auth_header" | jq -r .value)"
fi
[[ -n "$client_uuid" && -n "$client_secret" && "$client_secret" != null ]] \
  || fail "Keycloak gateway client is incomplete"

if oc -n "$candidate_namespace" get secret launchpad-public-access >/dev/null 2>&1; then
  cookie_secret="$(oc -n "$candidate_namespace" get secret launchpad-public-access \
    -o jsonpath='{.data.OIDC_COOKIE_SECRET}' | base64 --decode)"
else
  cookie_secret="$(openssl rand -base64 32 | tr -d '\n')"
fi
oc -n "$candidate_namespace" create secret generic launchpad-public-access \
  --from-literal=ACCESS_BROKER_KEY="$broker_key" \
  --from-literal=OIDC_CLIENT_SECRET="$client_secret" \
  --from-literal=OIDC_COOKIE_SECRET="$cookie_secret" \
  --dry-run=client -o yaml | oc apply -f - >/dev/null
unset admin_token auth_header admin_user broker_key client_secret cookie_secret realm clients executions flows

log "Binding Flightpath Keycloak to the candidate validation API"
oc -n "$keycloak_namespace" apply \
  -f "$repo_root/deploy/launchpad/overlays/flightpath-stage/network-policy.yaml" >/dev/null
oc -n "$keycloak_namespace" set env deployment/keycloak \
  "KC_HOSTNAME=$public_origin" \
  "KC_HOSTNAME_STRICT=true" \
  "KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true" \
  "LAUNCHPAD_ACCESS_VALIDATION_URL=http://backend.$candidate_namespace.svc:8000/api/v1/public-access/private/validate" >/dev/null
oc -n "$keycloak_namespace" rollout status deployment/keycloak --timeout=10m

log "Enabling the candidate public gateway and Flightpath-only placement"
oc -n "$candidate_namespace" patch configmap launchpad-config --type=merge --patch "$(jq -nc --arg origin "$public_origin" '{data:{PUBLIC_ACCESS_ENABLED:"true",PUBLIC_LABS_DOMAIN:"labs.smg-helix.ai",PUBLIC_LABS_SHARED_ORIGIN:$origin,PUBLIC_LABS_SHARED_PATH_MODE:"true",PUBLIC_ACCESS_PILOT_CLUSTER:"flightpath"}}')" >/dev/null
cluster_config="$(oc -n "$candidate_namespace" get configmap launchpad-cluster-targets -o jsonpath='{.data.clusters\.yaml}')"
cluster_patch="$(CLUSTER_CONFIG="$cluster_config" python3 -c '
import json, os, yaml
config = yaml.safe_load(os.environ["CLUSTER_CONFIG"])
targets = [item for item in config["clusters"] if item["cluster_id"] == "flightpath"]
if len(targets) != 1:
    raise SystemExit("Expected one Flightpath target")
target = targets[0]
target["public_access_enabled"] = True
target["public_ingress_domain"] = "labs.smg-helix.ai"
target["public_console_url"] = ""
target["public_oauth_url"] = ""
print(json.dumps({"data": {"clusters.yaml": yaml.safe_dump(config, sort_keys=False)}}))
')"
oc -n "$candidate_namespace" patch configmap launchpad-cluster-targets --type=merge --patch "$cluster_patch" >/dev/null

oc -n "$candidate_namespace" set env deployment/public-access-gateway --containers=oidc-proxy \
  "OAUTH2_PROXY_OIDC_ISSUER_URL=$public_origin/realms/launchpad-public" \
  "OAUTH2_PROXY_LOGIN_URL=$public_origin/realms/launchpad-public/protocol/openid-connect/auth" \
  "OAUTH2_PROXY_REDEEM_URL=$keycloak_internal/realms/launchpad-public/protocol/openid-connect/token" \
  "OAUTH2_PROXY_OIDC_JWKS_URL=$keycloak_internal/realms/launchpad-public/protocol/openid-connect/certs" \
  "OAUTH2_PROXY_REDIRECT_URL=$public_origin/oauth2/callback" \
  "OAUTH2_PROXY_SKIP_OIDC_DISCOVERY=true" \
  "OAUTH2_PROXY_INSECURE_OIDC_SKIP_ISSUER_VERIFICATION=false" >/dev/null

oc -n "$candidate_namespace" scale deployment/public-access-gateway --replicas=2 >/dev/null

for deployment in backend lifecycle-worker public-access-gateway; do
  oc -n "$candidate_namespace" rollout restart deployment/$deployment >/dev/null
  oc -n "$candidate_namespace" rollout status deployment/$deployment --timeout=10m
done

FLIGHTPATH_KUBECONFIG="$kubeconfig" "$repo_root/deploy/tunnel-oncluster/apply-flightpath.sh"

issuer="$(curl -fsS --retry 10 --retry-all-errors --retry-delay 2 \
  "$public_origin/realms/launchpad-public/.well-known/openid-configuration" | jq -r .issuer)"
[[ "$issuer" == "$public_origin/realms/launchpad-public" ]] \
  || fail "Unexpected public issuer: $issuer"

root_status="$(curl -sS -o /dev/null -w '%{http_code}' "$public_origin/")"
[[ "$root_status" =~ ^(200|302)$ ]] || fail "Unexpected public root status: $root_status"
log "Public edge, OIDC discovery, and Flightpath gateway are ready"
