#!/usr/bin/env bash
set -euo pipefail

: "${KUBECONFIG:?Set KUBECONFIG to the Arena kubeconfig before running this script}"

namespace=redhat-ods-applications
secret_name=mlflow-postgres
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "${script_dir}/.." && pwd)
manifest="${repo_root}/deploy/multicluster/arena-shared-mlflow.yaml"

if ! oc --kubeconfig="${KUBECONFIG}" get secret "${secret_name}" -n "${namespace}" >/dev/null 2>&1; then
  database_user=mlflow
  database_name=mlflow
  database_password=$(openssl rand -hex 32)
  backend_store_uri="postgresql://${database_user}:${database_password}@mlflow-postgres.${namespace}.svc.cluster.local:5432/${database_name}"

  oc --kubeconfig="${KUBECONFIG}" create secret generic "${secret_name}" \
    -n "${namespace}" \
    --from-literal=database-user="${database_user}" \
    --from-literal=database-password="${database_password}" \
    --from-literal=database-name="${database_name}" \
    --from-literal=backend-store-uri="${backend_store_uri}" \
    --dry-run=client -o yaml \
    | oc --kubeconfig="${KUBECONFIG}" apply -f - >/dev/null
fi

oc --kubeconfig="${KUBECONFIG}" apply -f "${manifest}"
oc --kubeconfig="${KUBECONFIG}" rollout status statefulset/mlflow-postgres \
  -n "${namespace}" --timeout=300s

generation=$(oc --kubeconfig="${KUBECONFIG}" get mlflow/mlflow -n "${namespace}" \
  -o jsonpath='{.metadata.generation}')
deadline=$((SECONDS + 300))
while ((SECONDS < deadline)); do
  operator_ready=$(oc --kubeconfig="${KUBECONFIG}" get mlflow/mlflow -n "${namespace}" \
    -o jsonpath='{.status.conditions[?(@.type=="MLflowOperatorReady")].status}')
  observed_generation=$(oc --kubeconfig="${KUBECONFIG}" get mlflow/mlflow -n "${namespace}" \
    -o jsonpath='{.status.conditions[?(@.type=="MLflowOperatorReady")].observedGeneration}')
  available=$(oc --kubeconfig="${KUBECONFIG}" get mlflow/mlflow -n "${namespace}" \
    -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
  migration=$(oc --kubeconfig="${KUBECONFIG}" get mlflow/mlflow -n "${namespace}" \
    -o jsonpath='{.status.conditions[?(@.type=="Migration")].status}')
  if [[ "${operator_ready}" == "True" && "${observed_generation}" == "${generation}" && "${available}" == "True" && "${migration}" == "True" ]]; then
    printf 'Arena shared MLflow is using its Secret-backed PostgreSQL service.\n'
    exit 0
  fi
  sleep 5
done

printf 'Timed out waiting for Arena shared MLflow generation %s.\n' "${generation}" >&2
exit 1
