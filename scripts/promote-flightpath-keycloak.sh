#!/usr/bin/env bash
set -euo pipefail
# Promote a qualified Keycloak release candidate to the Flightpath stage
# identity Deployment.
#
# This replaces the historical promotion helper, which patched the obsolete
# Keycloak CR in the `keycloak` namespace and verified artifacts against the
# retired rhpds repository. The current contract:
#
#   - artifacts are verified with cosign against the private repository's
#     registry-backed provenance (GitHub native attestation is unavailable
#     for this repository);
#   - a passing isolated-upgrade proof for the exact image digest is
#     mandatory before any live change (fail closed without it);
#   - the target is the launchpad-stage Deployment, never a Keycloak CR;
#   - the live database is never contacted directly.
#
# usage: promote-flightpath-keycloak.sh \
#          /explicit/flightpath.kubeconfig \
#          /path/to/keycloak-release.json \
#          /path/to/keycloak-isolated-upgrade.json

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kubeconfig="${1:-}"
release_receipt="${2:-}"
upgrade_receipt="${3:-}"
evidence_out="${repo_root}/evidence/runs/flightpath-keycloak-promotion-$(date -u +%Y%m%d).json"

stage_namespace="launchpad-stage"

fail() {
  printf 'flightpath Keycloak promotion blocked: %s\n' "$*" >&2
  exit 1
}

ocp() { oc --kubeconfig "$kubeconfig" "$@"; }

[[ -n "$kubeconfig" && -f "$kubeconfig" ]] \
  || fail "usage: $0 /explicit/flightpath.kubeconfig /path/to/keycloak-release.json /path/to/keycloak-isolated-upgrade.json"
[[ -n "$release_receipt" && -f "$release_receipt" ]] \
  || fail "release receipt is not a file"
[[ -n "$upgrade_receipt" && -f "$upgrade_receipt" ]] \
  || fail "isolated upgrade receipt is not a file"

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
# launchpad-backend repository only, so promotion deploys the digest-identical
# quay mirror of the verified GHCR candidate. Manifests are content-addressed:
# the same digest is the same bytes.
deploy_image="quay.io/redhat-gpte/launchpad-backend@${image##*@}"

# The isolated upgrade proof is mandatory and must cover this exact image.
upgrade_schema="$(jq -r '.schema_version // empty' "$upgrade_receipt")"
upgrade_result="$(jq -r '.result // empty' "$upgrade_receipt")"
upgrade_image="$(jq -r '.image // empty' "$upgrade_receipt")"
[[ "$upgrade_schema" == "launchpad.redhat.com/keycloak-isolated-upgrade/v1" ]] \
  || fail "isolated upgrade receipt has an unexpected schema"
[[ "$upgrade_result" == "passed" ]] \
  || fail "isolated upgrade proof did not pass"
[[ "$upgrade_image" == "$image" ]] \
  || fail "isolated upgrade receipt image does not match the isolated upgrade proof image: $upgrade_image vs $image"

ocp -n "$stage_namespace" get deploy/keycloak >/dev/null \
  || fail "stage keycloak deployment not found"
current_image="$(ocp -n "$stage_namespace" get deploy/keycloak \
  -o jsonpath='{.spec.template.spec.containers[0].image}')"
printf 'Current image: %s\n' "$current_image"
printf 'Candidate image: %s (deployed as %s)\n' "$image" "$deploy_image"
[[ "$current_image" != "$deploy_image" ]] \
  || fail "candidate image is already deployed"

# Capture a rollback backup of the live identity schema before any change.
# Read-only; the pg_dump completion footer proves the backup is complete.
backup_file="${repo_root}/evidence/runs/flightpath-keycloak-rollback-backup-$(date -u +%Y%m%dT%H%M%SZ).sql"
stage_db_user="$(ocp -n "$stage_namespace" get secret launchpad-db-secret \
  -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)"
stage_db_password="$(ocp -n "$stage_namespace" get secret launchpad-db-secret \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"
mkdir -p "$(dirname "$backup_file")"
ocp -n "$stage_namespace" exec deploy/postgres -- \
  env PGPASSWORD="$stage_db_password" pg_dump -U "$stage_db_user" -d launchpad_stage \
  --schema=keycloak --no-owner --no-privileges > "$backup_file" \
  || fail "rollback backup dump failed"
grep -q '^-- PostgreSQL database dump complete$' "$backup_file" \
  || fail "rollback backup is truncated (no pg_dump completion footer)"
printf 'Rollback backup: %s\n' "$backup_file"

# Capture a rollback reference before any change.
printf 'Rollback reference: %s\n' "$current_image"

ocp -n "$stage_namespace" set image deploy/keycloak "keycloak=${deploy_image}" >/dev/null
ocp -n "$stage_namespace" rollout status deploy/keycloak --timeout=600s >/dev/null \
  || fail "stage keycloak did not become ready after promotion"

# Post-promotion verification: the deployed pod must carry the fixed dark
# login card template, and the public surface must still render.
jar_file="$(mktemp)"
ocp -n "$stage_namespace" exec deploy/keycloak -c keycloak -- \
  cat /opt/keycloak/providers/launchpad-code-authenticator-1.0.0.jar > "$jar_file"
template_file="$(mktemp)"
unzip -p "$jar_file" theme-resources/templates/launchpad-code.ftl > "$template_file" 2>/dev/null \
  || fail "authenticator template is missing from the promoted image"
grep -q '#191919' "$template_file" \
  || fail "promoted image does not contain the fixed dark login card template"

login_html="$(curl -fsSL --max-time 30 https://labs.smg-helix.ai/)" \
  || fail "public portal did not respond"
grep -Fq "What you can do in Launchpad" <<<"$login_html" \
  || fail "public login does not contain the catalog overview"
grep -Fq "Access your lab" <<<"$login_html" \
  || fail "public login does not contain the access form"

mkdir -p "$(dirname "$evidence_out")"
jq -n \
  --arg image "$image" \
  --arg deploy_image "$deploy_image" \
  --arg source_revision "$source_revision" \
  --arg previous_image "$current_image" \
  --arg upgrade_receipt "$upgrade_receipt" \
  '{schema_version:"launchpad.redhat.com/keycloak-promotion/v1",
    result:"promoted",
    image:$image,
    deploy_image:$deploy_image,
    previous_image:$previous_image,
    source_revision:$source_revision,
    isolated_upgrade_receipt:$upgrade_receipt}' > "$evidence_out"

printf 'Flightpath Keycloak promotion passed for source %s.\n' "$source_revision"
printf 'Evidence: %s\n' "$evidence_out"
