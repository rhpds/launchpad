from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CHART = ROOT / "deploy/workloads/agentops-seat"
ARENA_ARGO_RBAC = ROOT / "deploy/multicluster/arena-argocd-rbac.yaml"

FORBIDDEN_CLUSTER_KINDS = {
    "ClusterRole",
    "ClusterRoleBinding",
    "ConsoleLink",
    "Namespace",
    "OperatorGroup",
    "Subscription",
}

OWNERSHIP_LABELS = {
    "app.kubernetes.io/managed-by": "launchpad",
    "launchpad.redhat.com/session-id": "session-1",
    "launchpad.redhat.com/workshop-id": "workshop-1",
    "launchpad.redhat.com/seat-id": "seat-1",
    "launchpad.redhat.com/tenant": "tenant-1",
    "launchpad.redhat.com/cluster-id": "arena",
}

IDENTITY_ARGS = [
    "--set",
    "identity.sessionId=session-1",
    "--set",
    "identity.workshopId=workshop-1",
    "--set",
    "identity.seatId=seat-1",
    "--set",
    "identity.tenantId=tenant-1",
    "--set",
    "identity.clusterId=arena",
]


def _render() -> tuple[str, list[dict[str, Any]]]:
    completed = subprocess.run(
        [
            "helm",
            "template",
            "agentops",
            str(CHART),
            "--namespace",
            "launchpad-agentops-seat-1",
            "--set",
            "runtime.existingSecret=agentops-runtime",
            *IDENTITY_ARGS,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    documents = [document for document in yaml.safe_load_all(completed.stdout) if document]
    return completed.stdout, documents


def test_agentops_seat_chart_lints_and_requires_an_existing_runtime_secret():
    subprocess.run(
        [
            "helm",
            "lint",
            str(CHART),
            "--set",
            "runtime.existingSecret=agentops-runtime",
            *IDENTITY_ARGS,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    failed = subprocess.run(
        ["helm", "template", "agentops", str(CHART), *IDENTITY_ARGS],
        check=False,
        capture_output=True,
        text=True,
    )

    assert failed.returncode != 0
    assert "runtime.existingSecret" in failed.stderr


def test_agentops_seat_chart_is_namespace_scoped_secret_free_and_owned():
    rendered, documents = _render()

    assert documents
    assert not ({document["kind"] for document in documents} & FORBIDDEN_CLUSTER_KINDS)
    assert "kind: Secret" not in rendered
    assert "changeme" not in rendered
    assert "thisisthepassword" not in rendered
    assert "paste-your-token-here" not in rendered
    assert "sk-" not in rendered

    for document in documents:
        labels = document.get("metadata", {}).get("labels", {})
        assert labels.items() >= OWNERSHIP_LABELS.items(), (
            document["kind"],
            document["metadata"]["name"],
        )


def test_agentops_seat_chart_contains_the_participant_runtime_and_routes():
    _, documents = _render()
    resources = {(document["kind"], document["metadata"]["name"]) for document in documents}

    assert {
        ("Deployment", "mortgage-ai-api"),
        ("Deployment", "mortgage-ai-ui"),
        ("Deployment", "minio"),
        ("Deployment", "agentops-grafana"),
        ("StatefulSet", "mortgage-ai-db"),
        ("DataSciencePipelinesApplication", "dspa"),
        ("Route", "mortgage-ai-ui-route"),
        ("Route", "grafana-route"),
        ("ServiceMonitor", "mortgage-ai-api"),
    }.issubset(resources)

    pod_specs = []
    for document in documents:
        if document["kind"] in {"Deployment", "StatefulSet"}:
            pod_specs.append(document["spec"]["template"]["spec"])
    images = [
        container["image"]
        for pod_spec in pod_specs
        for container in pod_spec.get("initContainers", []) + pod_spec.get("containers", [])
    ]
    assert images
    assert all(":latest" not in image for image in images)

    api = next(
        document
        for document in documents
        if document["kind"] == "Deployment" and document["metadata"]["name"] == "mortgage-ai-api"
    )
    api_container = api["spec"]["template"]["spec"]["containers"][0]
    assert {source["secretRef"]["name"] for source in api_container["envFrom"]} == {
        "agentops-runtime"
    }
    assert api["spec"]["strategy"] == {"type": "Recreate"}
    assert api_container["startupProbe"] == {
        "httpGet": {"path": "/health/", "port": "http"},
        "periodSeconds": 10,
        "failureThreshold": 90,
    }


def test_agentops_runtime_images_start_with_certified_resource_behavior():
    values = yaml.safe_load((CHART / "values.yaml").read_text())
    assert values["images"]["minioClient"] == (
        "quay.io/minio/mc:RELEASE.2023-06-19T19-31-19Z"
    )

    _, documents = _render()
    ui = next(
        document
        for document in documents
        if document["kind"] == "Deployment"
        and document["metadata"]["name"] == "mortgage-ai-ui"
    )
    ui_spec = ui["spec"]["template"]["spec"]
    nginx_init = next(
        container
        for container in ui_spec["initContainers"]
        if container["name"] == "configure-nginx-workers"
    )
    assert "worker_processes  1" in nginx_init["args"][0]
    assert {
        "name": "nginx-config",
        "mountPath": "/etc/nginx/nginx.conf",
        "subPath": "nginx.conf",
        "readOnly": True,
    } in ui_spec["containers"][0]["volumeMounts"]

    bootstrap = next(
        document
        for document in documents
        if document["kind"] == "Job" and document["metadata"]["name"] == "minio-bootstrap"
    )
    bootstrap_env = {
        item["name"]: item.get("value")
        for item in bootstrap["spec"]["template"]["spec"]["containers"][0]["env"]
    }
    assert bootstrap_env["MC_CONFIG_DIR"] == "/tmp/.mc"


def test_agentops_database_initializes_runtime_roles_before_migration():
    _, documents = _render()
    resources = {(document["kind"], document["metadata"]["name"]): document for document in documents}

    init_config = resources[("ConfigMap", "mortgage-ai-db-init")]
    init_script = init_config["data"]["10-create-runtime-roles.sh"]
    assert "LENDING_DB_PASSWORD" in init_script
    assert "COMPLIANCE_DB_PASSWORD" in init_script
    assert "CREATE ROLE lending_app" in init_script
    assert "CREATE ROLE compliance_app" in init_script
    assert "GRANT USAGE, CREATE ON SCHEMA public TO lending_app" in init_script

    database = resources[("StatefulSet", "mortgage-ai-db")]
    database_spec = database["spec"]["template"]["spec"]
    assert {
        "name": "init-scripts",
        "configMap": {"name": "mortgage-ai-db-init", "defaultMode": 365},
    } in database_spec["volumes"]

    api = resources[("Deployment", "mortgage-ai-api")]
    migration = next(
        container
        for container in api["spec"]["template"]["spec"]["initContainers"]
        if container["name"] == "migrate-database"
    )
    migration_database = next(item for item in migration["env"] if item["name"] == "DATABASE_URL")
    assert migration_database["valueFrom"]["secretKeyRef"]["key"] == "MIGRATION_DATABASE_URL"


def test_agentops_owns_a_supported_dspa_mariadb_and_normalizes_nfs_permissions():
    _, documents = _render()
    resources = {(document["kind"], document["metadata"]["name"]): document for document in documents}

    dspa = resources[("DataSciencePipelinesApplication", "dspa")]
    assert "mariaDB" not in dspa["spec"]["database"]
    assert dspa["spec"]["database"]["customExtraParams"] == '{"tls":"false"}'
    assert dspa["spec"]["database"]["externalDB"] == {
        "host": "agentops-pipeline-db.launchpad-agentops-seat-1.svc.cluster.local",
        "port": "3306",
        "pipelineDBName": "mlpipeline",
        "username": "mlpipeline",
        "passwordSecret": {
            "name": "agentops-runtime",
            "key": "MLPIPELINE_PASSWORD",
        },
    }

    postgres = resources[("StatefulSet", "mortgage-ai-db")]
    postgres_container = postgres["spec"]["template"]["spec"]["containers"][0]
    assert postgres_container["lifecycle"]["preStop"]["exec"]["command"] == [
        "/bin/sh",
        "-c",
        "chmod -R a+rwx /var/lib/postgresql/data || true",
    ]

    minio = resources[("Deployment", "minio")]
    minio_container = minio["spec"]["template"]["spec"]["containers"][0]
    assert minio_container["lifecycle"]["preStop"]["exec"]["command"] == [
        "/bin/sh",
        "-c",
        "chmod -R a+rwx /data || true",
    ]

    pipeline_db = resources[("Deployment", "agentops-pipeline-db")]
    pipeline_container = pipeline_db["spec"]["template"]["spec"]["containers"][0]
    assert pipeline_container["image"].startswith("registry.redhat.io/rhel9/mariadb-105@sha256:")
    assert pipeline_container["lifecycle"]["preStop"]["exec"]["command"] == [
        "/bin/sh",
        "-c",
        "chmod -R a+rwx /var/lib/mysql || true",
    ]
    pipeline_pvc = resources[("PersistentVolumeClaim", "pipeline-db-data")]
    assert pipeline_pvc["spec"]["storageClassName"] == "launchpad-nfs-ephemeral"


def test_agentops_grafana_can_read_only_its_seat_metrics():
    _, documents = _render()
    bindings = [document for document in documents if document["kind"] == "RoleBinding"]

    metrics_binding = next(
        binding for binding in bindings if binding["metadata"]["name"] == "agentops-grafana-metrics"
    )
    assert metrics_binding["roleRef"] == {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "ClusterRole",
        "name": "cluster-monitoring-view",
    }
    assert metrics_binding["subjects"] == [
        {
            "kind": "ServiceAccount",
            "name": "agentops-grafana",
            "namespace": "launchpad-agentops-seat-1",
        }
    ]


def test_agentops_api_has_only_namespace_scoped_mlflow_permissions():
    _, documents = _render()
    roles = {
        document["metadata"]["name"]: document
        for document in documents
        if document["kind"] == "Role"
    }
    bindings = {
        document["metadata"]["name"]: document
        for document in documents
        if document["kind"] == "RoleBinding"
    }

    role = roles["agentops-mlflow-client"]
    assert role["rules"] == [
        {
            "apiGroups": ["mlflow.kubeflow.org"],
            "resources": ["experiments", "datasets", "registeredmodels"],
            "verbs": ["get", "list", "create", "update", "delete"],
        }
    ]

    binding = bindings["agentops-mlflow-client"]
    assert binding["roleRef"] == {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "agentops-mlflow-client",
    }
    assert binding["subjects"] == [
        {
            "kind": "ServiceAccount",
            "name": "agentops-seat",
            "namespace": "launchpad-agentops-seat-1",
        }
    ]


def test_arena_argocd_can_manage_only_namespaced_monitoring_resources():
    documents = [
        document for document in yaml.safe_load_all(ARENA_ARGO_RBAC.read_text()) if document
    ]
    role = next(
        document
        for document in documents
        if document["kind"] == "ClusterRole"
        and document["metadata"]["name"] == "launchpad-argocd-manager"
    )

    monitoring_rule = next(
        rule for rule in role["rules"] if "monitoring.coreos.com" in rule["apiGroups"]
    )
    assert monitoring_rule["resources"] == ["servicemonitors"]
    assert set(monitoring_rule["verbs"]) == {"create", "update", "patch", "delete"}
