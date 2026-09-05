"""Component contract for Arena's RHOAI-managed shared MLflow pilot."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "deploy/multicluster/arena-shared-mlflow.yaml"
CLUSTER_REGISTRIES = (
    ROOT / "config/clusters.yaml",
    ROOT / "config/clusters-arena-cert.yaml",
    ROOT / "deploy/launchpad/overlays/arena/arena-clusters.yaml",
)
VALUES = ROOT / "deploy/workloads/agentops-seat/values.yaml"
CATALOG = ROOT / "catalog/agentops-observability/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/agentops-observability.yaml"


def test_shared_mlflow_uses_the_installed_rhoai_operator_and_disposable_storage():
    mlflow = yaml.safe_load(MANIFEST.read_text())

    assert mlflow["apiVersion"] == "mlflow.opendatahub.io/v1"
    assert mlflow["kind"] == "MLflow"
    assert mlflow["metadata"]["name"] == "mlflow"
    assert mlflow["metadata"]["namespace"] == "redhat-ods-applications"
    assert mlflow["metadata"]["labels"]["launchpad.redhat.com/shared-service"] == "true"

    spec = mlflow["spec"]
    assert spec["backendStoreUri"] == "sqlite:////mlflow/mlflow.db"
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
