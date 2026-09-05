"""Component contract for Arena's RHOAI-managed shared MLflow pilot."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "deploy/multicluster/arena-shared-mlflow.yaml"
BOOTSTRAP = ROOT / "scripts/configure-arena-shared-mlflow-postgres.sh"
CLUSTER_REGISTRIES = (
    ROOT / "config/clusters.yaml",
    ROOT / "config/clusters-arena-cert.yaml",
    ROOT / "deploy/launchpad/overlays/arena/arena-clusters.yaml",
)
VALUES = ROOT / "deploy/workloads/agentops-seat/values.yaml"
CATALOG = ROOT / "catalog/agentops-observability/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/agentops-observability.yaml"


def _resources() -> dict[tuple[str, str], dict]:
    resources = [item for item in yaml.safe_load_all(MANIFEST.read_text()) if item]
    return {(item["kind"], item["metadata"]["name"]): item for item in resources}


def test_shared_mlflow_uses_the_installed_rhoai_operator_and_postgres_secret():
    mlflow = _resources()[("MLflow", "mlflow")]

    assert mlflow["apiVersion"] == "mlflow.opendatahub.io/v1"
    assert mlflow["kind"] == "MLflow"
    assert mlflow["metadata"]["name"] == "mlflow"
    assert mlflow["metadata"]["namespace"] == "redhat-ods-applications"
    assert mlflow["metadata"]["labels"]["launchpad.redhat.com/shared-service"] == "true"

    spec = mlflow["spec"]
    assert "backendStoreUri" not in spec
    assert spec["backendStoreUriFrom"] == {
        "name": "mlflow-postgres",
        "key": "backend-store-uri",
    }
    assert spec["caBundleConfigMap"] == {"name": "mlflow-postgres-ca"}
    assert spec["serveArtifacts"] is True
    assert spec["artifactsDestination"] == "file:///mlflow/artifacts"
    assert spec["replicas"] == 1
    assert spec["workers"] == 2
    assert spec["storage"]["storageClassName"] == "launchpad-nfs-ephemeral"
    assert spec["storage"]["accessModes"] == ["ReadWriteOnce"]
    assert spec["storage"]["resources"]["requests"]["storage"] == "20Gi"
    assert spec["workspaceLabelSelector"]["matchExpressions"] == [
        {
            "key": "launchpad.redhat.com/session-id",
            "operator": "Exists",
        }
    ]


def test_shared_mlflow_postgres_is_persistent_restricted_and_not_secret_in_git():
    resources = _resources()
    statefulset = resources[("StatefulSet", "mlflow-postgres")]
    service = resources[("Service", "mlflow-postgres")]
    policy = resources[("NetworkPolicy", "mlflow-postgres")]
    disruption_budget = resources[("PodDisruptionBudget", "mlflow-postgres")]

    container = statefulset["spec"]["template"]["spec"]["containers"][0]
    assert "postgresql-16@sha256:" in container["image"]
    assert container["securityContext"] == {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
    }
    assert statefulset["spec"]["volumeClaimTemplates"][0]["spec"] == {
        "accessModes": ["ReadWriteOnce"],
        "storageClassName": "nfs-storage",
        "resources": {"requests": {"storage": "50Gi"}},
    }
    assert service["spec"]["ports"][0]["port"] == 5432
    assert policy["spec"]["ingress"][0]["from"][0]["podSelector"] == {
        "matchLabels": {"app": "mlflow"}
    }
    assert disruption_budget["spec"]["minAvailable"] == 1
    assert not any(kind == "Secret" for kind, _name in resources)
    assert "postgresql://" not in MANIFEST.read_text()


def test_shared_mlflow_postgres_uses_openshift_service_ca_tls():
    resources = _resources()
    statefulset = resources[("StatefulSet", "mlflow-postgres")]
    service = resources[("Service", "mlflow-postgres")]
    ca_bundle = resources[("ConfigMap", "mlflow-postgres-ca")]

    assert service["metadata"]["annotations"] == {
        "service.beta.openshift.io/serving-cert-secret-name": "mlflow-postgres-tls"
    }
    assert ca_bundle["metadata"]["annotations"] == {
        "service.beta.openshift.io/inject-cabundle": "true"
    }
    assert "data" not in ca_bundle

    pod_spec = statefulset["spec"]["template"]["spec"]
    init_container = pod_spec["initContainers"][0]
    assert init_container["name"] == "prepare-postgresql-tls"
    assert init_container["securityContext"] == {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
    }
    assert "chmod 0600 /work/tls.key" in init_container["command"][2]

    container = pod_spec["containers"][0]
    assert container["command"] == ["/usr/bin/run-postgresql"]
    assert container["args"] == [
        "-c",
        "ssl=on",
        "-c",
        "ssl_min_protocol_version=TLSv1.2",
        "-c",
        "ssl_cert_file=/var/run/postgresql-tls/tls.crt",
        "-c",
        "ssl_key_file=/var/run/postgresql-tls/tls.key",
    ]
    assert "sslmode=require" in container["readinessProbe"]["exec"]["command"][2]
    assert {mount["name"] for mount in container["volumeMounts"]} >= {
        "postgres-data",
        "postgresql-tls",
    }
    assert {volume["name"] for volume in pod_spec["volumes"]} == {
        "postgresql-serving-cert",
        "postgresql-tls",
    }
    serving_cert = next(
        volume for volume in pod_spec["volumes"] if volume["name"] == "postgresql-serving-cert"
    )
    assert serving_cert["secret"]["secretName"] == "mlflow-postgres-tls"


def test_postgres_bootstrap_generates_the_secret_without_printing_credentials():
    script = BOOTSTRAP.read_text()

    assert ': "${KUBECONFIG:?' in script
    assert "openssl rand -hex 32" in script
    assert "backend-store-uri" in script
    assert "create secret generic" in script
    assert "apply -f" in script
    assert "set -x" not in script
    assert "echo ${" not in script
    assert "observedGeneration" in script
    assert 'type=="MLflowOperatorReady"' in script
    assert "Migration" in script


def test_arena_registry_publishes_the_rhoai_and_mlflow_services():
    for path in CLUSTER_REGISTRIES:
        document = yaml.safe_load(path.read_text())
        registry = document.get("data", {}).get("clusters.yaml", document)
        if isinstance(registry, str):
            registry = yaml.safe_load(registry)
        arena = next(
            cluster for cluster in registry["clusters"] if cluster["cluster_id"] == "arena"
        )

        assert set(arena["capabilities"]) >= {
            "mlflow",
            "rhoai",
            "user_workload_monitoring",
            "data_science_pipelines",
        }
        assert arena["service_urls"]["mlflow"] == (
            "https://rh-ai.apps.arena.fm2aihpcsed.com/mlflow"
        )
        assert arena["service_urls"]["rhoai"] == (
            "https://rh-ai.apps.arena.fm2aihpcsed.com/"
        )


def test_agentops_uses_the_operator_published_internal_mlflow_path():
    expected = "https://mlflow.redhat-ods-applications.svc.cluster.local:8443/mlflow"
    values = yaml.safe_load(VALUES.read_text())
    catalog = yaml.safe_load(CATALOG.read_text())
    intake = yaml.safe_load(INTAKE.read_text())

    assert values["mlflow"]["trackingUri"] == expected
    assert (
        catalog["metadata"]["workload_runtime_secret_sources"]["MLFLOW_TRACKING_URI"][
            "value"
        ]
        == expected
    )
    assert (
        intake["runtime"]["workload"]["runtime_secret_sources"][
            "MLFLOW_TRACKING_URI"
        ]["value"]
        == expected
    )
