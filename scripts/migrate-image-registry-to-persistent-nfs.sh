#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:?KUBECONFIG must point to an explicit cluster administrator kubeconfig}"
storage_class="${1:-nfs-storage}"
size="${2:-100Gi}"
claim="${3:-launchpad-image-registry-storage}"
namespace="openshift-image-registry"
migration_pod="image-registry-storage-migrate"
migration_policy="image-registry-storage-migrate"

if [[ ! -s "$KUBECONFIG" ]]; then
  echo "KUBECONFIG does not exist or is empty" >&2
  exit 2
fi
if ! [[ "$size" =~ ^[1-9][0-9]*(Gi|Ti)$ ]]; then
  echo "size must be a positive Gi or Ti quantity" >&2
  exit 2
fi

cleanup() {
  oc --kubeconfig "$KUBECONFIG" -n "$namespace" delete pod "$migration_pod" \
    --ignore-not-found --wait=false >/dev/null 2>&1 || true
  oc --kubeconfig "$KUBECONFIG" -n "$namespace" delete \
    "networkpolicy/$migration_policy" --ignore-not-found --wait=false \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT

current_claim="$(
  oc --kubeconfig "$KUBECONFIG" \
    get configs.imageregistry.operator.openshift.io cluster \
    -o jsonpath='{.spec.storage.pvc.claim}'
)"

oc --kubeconfig "$KUBECONFIG" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $claim
  namespace: $namespace
  labels:
    app.kubernetes.io/managed-by: launchpad
    app.kubernetes.io/part-of: partner-ai-launchpad
    launchpad.redhat.com/purpose: durable-image-registry
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: "$storage_class"
  resources:
    requests:
      storage: "$size"
EOF

oc --kubeconfig "$KUBECONFIG" -n "$namespace" wait \
  --for=jsonpath='{.status.phase}'=Bound "pvc/$claim" --timeout=180s >/dev/null

if [[ "$current_claim" != "$claim" ]]; then
  registry_image="$(
    oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
      get deployment/image-registry \
      -o jsonpath='{.spec.template.spec.containers[?(@.name=="registry")].image}'
  )"
  if [[ -z "$registry_image" ]]; then
    echo "could not resolve the current registry image" >&2
    exit 3
  fi

  cleanup
  oc --kubeconfig "$KUBECONFIG" apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: $migration_pod
  namespace: $namespace
  labels:
    app.kubernetes.io/managed-by: launchpad
    launchpad.redhat.com/purpose: image-registry-storage-migration
spec:
  restartPolicy: Never
  serviceAccountName: registry
  containers:
    - name: storage
      image: $registry_image
      imagePullPolicy: IfNotPresent
      command: ["/bin/sh", "-c", "while true; do sleep 3600; done"]
      volumeMounts:
        - name: target
          mountPath: /target
  volumes:
    - name: target
      persistentVolumeClaim:
        claimName: $claim
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: $migration_policy
  namespace: $namespace
  labels:
    app.kubernetes.io/managed-by: launchpad
    launchpad.redhat.com/purpose: image-registry-storage-migration
spec:
  podSelector:
    matchLabels:
      launchpad.redhat.com/purpose: image-registry-storage-migration
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: $namespace
      ports:
        - protocol: TCP
          port: 18080
EOF
  oc --kubeconfig "$KUBECONFIG" -n "$namespace" wait \
    --for=condition=Ready "pod/$migration_pod" --timeout=180s >/dev/null

  source_files="$(
    oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
      exec deployment/image-registry -c registry -- \
      sh -c 'find /registry -type f | wc -l'
  )"
  if [[ "$source_files" -lt 1 ]]; then
    echo "refusing to migrate an empty registry" >&2
    exit 3
  fi

  target_ip="$(
    oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
      get "pod/$migration_pod" -o jsonpath='{.status.podIP}'
  )"
  if ! [[ "$target_ip" =~ ^[0-9a-fA-F:.]+$ ]]; then
    echo "migration pod has no valid pod IP" >&2
    exit 3
  fi

  # Keep the blob stream inside the cluster. Routing tar through two `oc exec`
  # connections sends every byte across the administrator workstation and is
  # prohibitively slow over VPN.
  oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
    exec "pod/$migration_pod" -c storage -- \
    sh -c 'socat -u TCP-LISTEN:18080,reuseaddr STDOUT | tar --no-same-owner --no-same-permissions --no-overwrite-dir --touch -C /target -xf -' &
  receiver_pid="$!"
  sleep 2
  if ! oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
    exec deployment/image-registry -c registry -- \
    sh -c 'tar -C /registry -cf - . | socat -u STDIN "TCP:$1:18080"' sh "$target_ip"; then
    kill "$receiver_pid" 2>/dev/null || true
    wait "$receiver_pid" 2>/dev/null || true
    echo "in-cluster registry copy failed" >&2
    exit 3
  fi
  wait "$receiver_pid"
  oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
    exec "pod/$migration_pod" -c storage -- sync

  target_files="$(
    oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
      exec "pod/$migration_pod" -c storage -- \
      sh -c 'find /target -type f | wc -l'
  )"
  if [[ "$target_files" -ne "$source_files" ]]; then
    echo "registry copy verification failed: source=$source_files target=$target_files" >&2
    exit 3
  fi

  cleanup
  patch="$(
    printf '{"spec":{"storage":{"emptyDir":null,"pvc":{"claim":"%s"}}}}' \
      "$claim"
  )"
  oc --kubeconfig "$KUBECONFIG" patch \
    configs.imageregistry.operator.openshift.io cluster \
    --type=merge --patch "$patch" >/dev/null
fi

for _attempt in {1..60}; do
  deployment_claim="$(
    oc --kubeconfig "$KUBECONFIG" -n "$namespace" \
      get deployment/image-registry \
      -o jsonpath='{.spec.template.spec.volumes[?(@.name=="registry-storage")].persistentVolumeClaim.claimName}'
  )"
  [[ "$deployment_claim" == "$claim" ]] && break
  sleep 5
done
if [[ "${deployment_claim:-}" != "$claim" ]]; then
  echo "registry deployment did not mount PVC '$claim'" >&2
  exit 4
fi

oc --kubeconfig "$KUBECONFIG" -n "$namespace" rollout status \
  deployment/image-registry --timeout=300s >/dev/null

# A second restart is the persistence proof: the registry must become ready
# again with the same PVC after its pod-local filesystem is discarded.
oc --kubeconfig "$KUBECONFIG" -n "$namespace" rollout restart \
  deployment/image-registry >/dev/null
oc --kubeconfig "$KUBECONFIG" -n "$namespace" rollout status \
  deployment/image-registry --timeout=300s >/dev/null

operator="$(
  oc --kubeconfig "$KUBECONFIG" \
    get configs.imageregistry.operator.openshift.io cluster -o json
)"
available="$(printf '%s' "$operator" | jq -r '.status.conditions[] | select(.type=="Available") | .status')"
degraded="$(printf '%s' "$operator" | jq -r '.status.conditions[] | select(.type=="Degraded") | .status')"
configured_claim="$(printf '%s' "$operator" | jq -r '.spec.storage.pvc.claim // ""')"
if [[ "$available" != "True" || "$degraded" != "False" || "$configured_claim" != "$claim" ]]; then
  echo "registry operator is not healthy on the persistent claim" >&2
  exit 4
fi

printf 'persistent-registry\tclaim=%s\tclass=%s\tsize=%s\tavailable=%s\tdegraded=%s\n' \
  "$claim" "$storage_class" "$size" "$available" "$degraded"
