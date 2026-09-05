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
