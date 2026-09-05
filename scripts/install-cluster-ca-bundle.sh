#!/usr/bin/env bash
set -euo pipefail

control_kubeconfig="${1:?usage: install-cluster-ca-bundle.sh <control-kubeconfig> <namespace> <deployment> <ingress-ca-kubeconfig>...}"
namespace="${2:?namespace is required}"
deployment="${3:?deployment is required}"
shift 3
if [[ "$#" -lt 1 ]]; then
  echo "at least one ingress CA kubeconfig is required" >&2
  exit 2
fi
for kubeconfig in "$control_kubeconfig" "$@"; do
  if [[ ! -s "$kubeconfig" ]]; then
    echo "kubeconfig does not exist or is empty: $kubeconfig" >&2
    exit 2
  fi
done

tmp_dir="$(mktemp -d)"
bundle="$tmp_dir/ca-bundle.crt"
trap 'rm -rf "$tmp_dir"' EXIT

# Start with the backend image's system roots, then append every execution
# cluster's default ingress chain. CA material is public; credentials remain in
# the caller-provided kubeconfig files and are never copied or printed.
oc --kubeconfig "$control_kubeconfig" -n "$namespace" \
  exec "deployment/$deployment" -- \
  cat /etc/pki/tls/certs/ca-bundle.crt > "$bundle"
for kubeconfig in "$@"; do
  printf '\n' >> "$bundle"
  oc --kubeconfig "$kubeconfig" -n openshift-config-managed \
    get configmap default-ingress-cert \
    -o go-template='{{index .data "ca-bundle.crt"}}' >> "$bundle"
done

oc --kubeconfig "$control_kubeconfig" -n "$namespace" \
  create configmap launchpad-cluster-ca-bundle \
  --from-file="ca-bundle.crt=$bundle" \
  --dry-run=client -o yaml \
  | oc --kubeconfig "$control_kubeconfig" apply -f - >/dev/null

oc --kubeconfig "$control_kubeconfig" -n "$namespace" \
  set volume "deployment/$deployment" --add --overwrite \
  --name=cluster-ca-bundle \
  --type=configmap \
  --configmap-name=launchpad-cluster-ca-bundle \
  --mount-path=/etc/launchpad-ca \
  --read-only=true >/dev/null
oc --kubeconfig "$control_kubeconfig" -n "$namespace" \
  set env "deployment/$deployment" \
  SSL_CERT_FILE=/etc/launchpad-ca/ca-bundle.crt \
  REQUESTS_CA_BUNDLE=/etc/launchpad-ca/ca-bundle.crt >/dev/null
oc --kubeconfig "$control_kubeconfig" -n "$namespace" \
  rollout status "deployment/$deployment" --timeout=180s >/dev/null

printf 'cluster-ca-bundle\tcertificates=%s\tsha256=%s\n' \
  "$(grep -c 'BEGIN CERTIFICATE' "$bundle")" \
  "$(shasum -a 256 "$bundle" | awk '{print $1}')"
