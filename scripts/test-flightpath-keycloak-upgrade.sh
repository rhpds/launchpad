#!/usr/bin/env bash
set -euo pipefail
# Isolated Keycloak upgrade proof for the Flightpath stage identity service.
#
# Restores a read-only copy of the live keycloak schema into a disposable
# namespace, starts the release candidate against that copy, and proves the
# upgrade, schema migration, data integrity, authenticator artifact and
# theme deployment before any live promotion decision. The live identity
# service and its database are never mutated: the live postgres is contacted
# only through a read-only pg_dump.
#
# usage: test-flightpath-keycloak-upgrade.sh \
#          /explicit/flightpath.kubeconfig \
#          /path/to/keycloak-release.json \
#          [output-receipt.json]

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kubeconfig="${1:-}"
release_receipt="${2:-}"
receipt_out="${3:-${repo_root}/evidence/runs/flightpath-keycloak-isolated-upgrade-$(date -u +%Y%m%d).json}"

test_namespace="launchpad-keycloak-upgrade-test"
live_namespace="launchpad-stage"
live_database="launchpad_stage"
live_db_secret="launchpad-db-secret"
provider_jar="launchpad-code-authenticator-1.0.0.jar"

fail() {
  printf 'flightpath Keycloak isolated upgrade test blocked: %s\n' "$*" >&2
  exit 1
}

ocp() { oc --kubeconfig "$kubeconfig" "$@"; }

[[ -n "$kubeconfig" && -f "$kubeconfig" ]] \
  || fail "usage: $0 /explicit/flightpath.kubeconfig /path/to/keycloak-release.json [output-receipt.json]"
[[ -n "$release_receipt" && -f "$release_receipt" ]] \
  || fail "release receipt is not a file"

server="$(ocp whoami --show-server)"
[[ "$server" == "https://api.flightpath.fm2aihpcsed.com:6443" ]] \
  || fail "kubeconfig is not Flightpath"

schema="$(jq -r '.schema_version // empty' "$release_receipt")"
source_revision="$(jq -r '.source_revision // empty' "$release_receipt")"
image="$(jq -r '.image // empty' "$release_receipt")"
platform="$(jq -r '.platform // empty' "$release_receipt")"
published="$(jq -r '.published // false' "$release_receipt")"

[[ "$schema" == "launchpad.redhat.com/keycloak-release/v1" ]] \
  || fail "unexpected receipt schema"
[[ "$source_revision" =~ ^[0-9a-f]{40}$ ]] \
  || fail "source revision is not immutable"
[[ "$image" =~ ^ghcr\.io/jkershawrh/launchpad-keycloak@sha256:[0-9a-f]{64}$ ]] \
  || fail "image is not an approved immutable GHCR reference"
[[ "$platform" == "linux/amd64" && "$published" == "true" ]] \
  || fail "release is not a published linux/amd64 artifact"

command -v cosign >/dev/null || fail "cosign is required for signature verification"
identity_regexp='^https://github\.com/jkershawrh/intel-ai-launchpad/\.github/workflows/keycloak-release\.yml@refs/(heads|tags)/.+$'
cosign verify "$image" \
  --certificate-identity-regexp "$identity_regexp" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com >/dev/null \
  || fail "keyless signature verification failed"
provenance_file="$(mktemp)"
cosign verify-attestation --type slsaprovenance \
  --certificate-identity-regexp "$identity_regexp" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  "$image" > "$provenance_file" \
  || fail "registry-backed provenance verification failed"
jq -se --arg expected "$source_revision" \
  '[.[] | (if type == "array" then .[] else . end)
    | .payload | @base64d | fromjson
    | .predicate.invocation.configSource.digest.sha1 == $expected]
   | length > 0 and all' "$provenance_file" \
  || fail "provenance does not match the release source revision"

# The Flightpath pull robot holds quay credentials scoped to the established
# launchpad-backend repository only, so the qualified GHCR candidate is
# deployed through its digest-identical quay mirror. Manifests are
# content-addressed: the same digest is the same bytes.
deploy_image="quay.io/redhat-gpte/launchpad-backend@${image##*@}"

# The live stage identity must exist; this is read-only presence checking.
ocp -n "$live_namespace" get deploy/keycloak >/dev/null \
  || fail "live stage keycloak deployment not found"
ocp -n "$live_namespace" get deploy/postgres >/dev/null \
  || fail "live stage postgres not found"

# Zero-residue teardown even when a later step fails.
cleanup() {
  ocp delete namespace "$test_namespace" --ignore-not-found --wait=true >/dev/null 2>&1
}
trap cleanup EXIT

ocp delete namespace "$test_namespace" --ignore-not-found --wait=true >/dev/null
ocp create namespace "$test_namespace" >/dev/null

test_db_user="keycloak_test"
test_db_password="$(openssl rand -hex 24)"
test_admin_password="$(openssl rand -hex 16)"
test_broker_key="$(openssl rand -hex 24)"
ocp -n "$test_namespace" create secret generic keycloak-upgrade-db \
  --from-literal=POSTGRES_USER="$test_db_user" \
  --from-literal=POSTGRES_PASSWORD="$test_db_password" \
  --from-literal=POSTGRES_DB="$live_database" >/dev/null
ocp -n "$test_namespace" create secret generic keycloak-upgrade-bootstrap \
  --from-literal=username=keycloak-test-admin \
  --from-literal=password="$test_admin_password" \
  --from-literal=broker-key="$test_broker_key" >/dev/null

# The candidate image lives in the private GHCR registry; copy the stage pull
# robot's dockerconfig secret so the isolated namespace can pull it.
ocp -n "$live_namespace" get secret launchpad-registry-pull -o json \
  | jq 'del(.metadata.namespace, .metadata.resourceVersion, .metadata.uid,
            .metadata.creationTimestamp, .metadata.managedFields)' \
  | ocp -n "$test_namespace" apply -f - >/dev/null \
  || fail "copying the registry pull secret into the isolated namespace failed"

ocp -n "$test_namespace" create -f - >/dev/null <<'POSTGRES'
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app.kubernetes.io/name: postgres
  ports:
    - {name: postgres, port: 5432, targetPort: 5432}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  strategy: {type: Recreate}
  selector:
    matchLabels:
      app.kubernetes.io/name: postgres
  template:
    metadata:
      labels:
        app.kubernetes.io/name: postgres
        app.kubernetes.io/component: database
    spec:
      containers:
        - name: postgres
          image: docker.io/library/postgres@sha256:075f7ba66bc9b3ce7d6b8b635208ff61cd7cf1a67d71ec530eec5d7ae0cbe571
          env:
            - {name: PGDATA, value: /var/lib/postgresql/data/pgdata}
            - name: POSTGRES_DB
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-db, key: POSTGRES_DB}}
            - name: POSTGRES_USER
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-db, key: POSTGRES_USER}}
            - name: POSTGRES_PASSWORD
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-db, key: POSTGRES_PASSWORD}}
          ports:
            - {name: postgres, containerPort: 5432}
          readinessProbe:
            exec: {command: [pg_isready, -U, keycloak_test, -d, launchpad_stage]}
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests: {cpu: 250m, memory: 256Mi}
            limits: {cpu: "1", memory: 1Gi}
POSTGRES

ocp -n "$test_namespace" rollout status deploy/postgres --timeout=180s >/dev/null \
  || fail "isolated postgres did not become ready"

# Read-only dump of the live keycloak schema. Credentials never reach the
# terminal or the receipt.
live_db_user="$(ocp -n "$live_namespace" get secret "$live_db_secret" \
  -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)"
live_db_password="$(ocp -n "$live_namespace" get secret "$live_db_secret" \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"

dump_file="$(mktemp)"
# NOTE: no -i on this exec — oc exec with an allocated-but-empty stdin truncates
# the stdout stream; the footer and fidelity checks below still guard the result.
ocp -n "$live_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$live_db_password" pg_dump -U "$live_db_user" -d "$live_database" \
  --schema=keycloak --no-owner --no-privileges > "$dump_file" \
  || fail "read-only dump of the live keycloak schema failed"
[[ -s "$dump_file" ]] || fail "live keycloak schema dump is empty"
# A truncated stream can exit zero; only the completion footer proves the dump
# finished (pg_dump 16 emits the footer followed by a \unrestrict guard line).
grep -q '^-- PostgreSQL database dump complete$' "$dump_file" \
  || fail "live keycloak schema dump is truncated (no pg_dump completion footer)"
grep -q '^COPY keycloak.user_entity ' "$dump_file" \
  || fail "live keycloak schema dump is missing the user entity table data"

# Live baseline counts (read-only) prove restore fidelity later.
live_user_count="$(ocp -n "$live_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$live_db_password" psql -U "$live_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.user_entity')"
live_realm_count="$(ocp -n "$live_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$live_db_password" psql -U "$live_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.realm')"
live_client_count="$(ocp -n "$live_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$live_db_password" psql -U "$live_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.client')"

ocp -n "$test_namespace" exec -i deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" \
  -v ON_ERROR_STOP=1 < "$dump_file" >/dev/null \
  || fail "restoring the live keycloak schema copy into the isolated database failed"

baseline_user_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.user_entity')"
baseline_realm_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.realm')"
baseline_client_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.client')"
[[ "$baseline_user_count" =~ ^[0-9]+$ ]] \
  || fail "restored copy user count is not a number"
[[ "$baseline_realm_count" =~ ^[0-9]+$ && "$baseline_realm_count" -gt 0 ]] \
  || fail "restored copy has no realms"
# The isolated copy must match the live database exactly before any upgrade.
[[ "$baseline_user_count" == "$live_user_count" ]] \
  || fail "restore fidelity: user entities $live_user_count live vs $baseline_user_count restored"
[[ "$baseline_realm_count" == "$live_realm_count" ]] \
  || fail "restore fidelity: realms $live_realm_count live vs $baseline_realm_count restored"
[[ "$baseline_client_count" == "$live_client_count" ]] \
  || fail "restore fidelity: clients $live_client_count live vs $baseline_client_count restored"
printf 'Restored baseline matches live: %s realms, %s clients, %s user entities.\n' \
  "$baseline_realm_count" "$baseline_client_count" "$baseline_user_count"

# The candidate runs against the isolated database copy only.
ocp -n "$test_namespace" create -f - >/dev/null <<KEYCLOAK
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: keycloak
  template:
    metadata:
      labels:
        app.kubernetes.io/name: keycloak
        app.kubernetes.io/component: identity
    spec:
      imagePullSecrets:
        - name: launchpad-registry-pull
      containers:
        - name: keycloak
          image: ${deploy_image}
          args: [start, --optimized]
          env:
            - {name: KC_DB, value: postgres}
            - {name: KC_DB_URL, value: jdbc:postgresql://postgres:5432/${live_database}}
            - {name: KC_DB_SCHEMA, value: keycloak}
            - name: KC_DB_USERNAME
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-db, key: POSTGRES_USER}}
            - name: KC_DB_PASSWORD
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-db, key: POSTGRES_PASSWORD}}
            - {name: KC_HTTP_ENABLED, value: "true"}
            - {name: KC_HEALTH_ENABLED, value: "true"}
            - {name: KC_HOSTNAME_STRICT, value: "false"}
            - {name: KC_PROXY_HEADERS, value: xforwarded}
            - name: KC_BOOTSTRAP_ADMIN_USERNAME
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-bootstrap, key: username}}
            - name: KC_BOOTSTRAP_ADMIN_PASSWORD
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-bootstrap, key: password}}
            - {name: LAUNCHPAD_ACCESS_VALIDATION_URL, value: http://backend.launchpad-flightpath-candidate.svc:8000/api/v1/public-access/private/validate}
            - name: ACCESS_BROKER_KEY
              valueFrom: {secretKeyRef: {name: keycloak-upgrade-bootstrap, key: broker-key}}
          ports:
            - {name: http, containerPort: 8080}
            - {name: management, containerPort: 9000}
          readinessProbe:
            httpGet: {path: /health/ready, port: management}
            initialDelaySeconds: 15
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 24
          resources:
            requests: {cpu: 250m, memory: 768Mi}
            limits: {cpu: "2", memory: 2Gi}
KEYCLOAK

ocp -n "$test_namespace" rollout status deploy/keycloak --timeout=420s >/dev/null \
  || fail "candidate keycloak did not become ready against the restored data"

# Schema migration must complete without errors.
if ocp -n "$test_namespace" logs deploy/keycloak | grep -E 'ERROR|Migration failed'; then
  fail "candidate keycloak logged migration errors"
fi
printf 'Migration log clean.\n'

# Data integrity: the patch upgrade must not change realm, client or user counts.
upgraded_user_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.user_entity')"
upgraded_realm_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.realm')"
upgraded_client_count="$(ocp -n "$test_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$test_db_password" psql -U "$test_db_user" -d "$live_database" -tAc \
  'select count(*) from keycloak.client')"
[[ "$upgraded_user_count" == "$baseline_user_count" ]] \
  || fail "user entity count changed during upgrade: $baseline_user_count -> $upgraded_user_count"
[[ "$upgraded_realm_count" == "$baseline_realm_count" ]] \
  || fail "realm count changed during upgrade: $baseline_realm_count -> $upgraded_realm_count"
[[ "$upgraded_client_count" == "$baseline_client_count" ]] \
  || fail "client count changed during upgrade: $baseline_client_count -> $upgraded_client_count"

# The candidate pod must carry the qualified authenticator artifact and the
# fixed dark login card template (the 08f8655f contrast fix). The image is
# minimal, so the provider jar is streamed out and inspected locally.
jar_file="$(mktemp)"
ocp -n "$test_namespace" exec deploy/keycloak -c keycloak -- \
  cat "/opt/keycloak/providers/${provider_jar}" > "$jar_file"
[[ -s "$jar_file" ]] \
  || fail "authenticator provider jar is missing from the deployed image"
template_file="$(mktemp)"
unzip -p "$jar_file" theme-resources/templates/launchpad-code.ftl > "$template_file" 2>/dev/null \
  || fail "authenticator template is missing from the provider jar"
grep -q '#191919' "$template_file" \
  || fail "deployed image does not contain the fixed dark login card template"
grep -q 'launchpad-code' "$template_file" \
  || fail "authenticator template content is unexpected"

mkdir -p "$(dirname "$receipt_out")"
jq -n \
  --arg image "$image" \
  --arg deploy_image "$deploy_image" \
  --arg source_revision "$source_revision" \
  --arg namespace "$test_namespace" \
  --argjson realms "$upgraded_realm_count" \
  --argjson clients "$upgraded_client_count" \
  --argjson users "$upgraded_user_count" \
  '{schema_version:"launchpad.redhat.com/keycloak-isolated-upgrade/v1",
    result:"passed",
    image:$image,
    deploy_image:$deploy_image,
    source_revision:$source_revision,
    namespace:$namespace,
    realm_count:$realms,
    client_count:$clients,
    user_entity_count:$users,
    migration_errors:false,
    restore_fidelity_verified:true,
    dark_card_template_verified:true}' > "$receipt_out"

ocp delete namespace "$test_namespace" --wait=true >/dev/null
[[ -z "$(ocp get namespace "$test_namespace" --ignore-not-found -o name)" ]] \
  || fail "isolated test namespace was not removed"
trap - EXIT

printf 'Flightpath Keycloak isolated upgrade proof PASSED for %s.\n' "$source_revision"
printf 'Receipt: %s\n' "$receipt_out"
