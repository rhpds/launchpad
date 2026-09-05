"""Contracts for Arena's supported one-seat OpenShift Logging pilot."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OPERATORS = ROOT / "deploy/multicluster/arena-agentops-logging-operators.yaml"
PILOT = ROOT / "deploy/multicluster/arena-agentops-logging-pilot.yaml"


def _documents(path: Path) -> list[dict]:
    return [document for document in yaml.safe_load_all(path.read_text()) if document]


def test_logging_operators_use_matching_supported_red_hat_channels():
    documents = _documents(OPERATORS)
    namespaces = {
        document["metadata"]["name"]
        for document in documents
        if document["kind"] == "Namespace"
    }
    assert namespaces == {"openshift-operators-redhat", "openshift-logging"}

    operator_groups = {
        document["metadata"]["namespace"]: document
        for document in documents
        if document["kind"] == "OperatorGroup"
    }
    assert set(operator_groups) == {"openshift-operators-redhat", "openshift-logging"}

    subscriptions = {
        document["metadata"]["name"]: document
        for document in documents
        if document["kind"] == "Subscription"
    }
    assert set(subscriptions) == {
        "loki-operator",
        "cluster-logging",
        "cluster-observability-operator",
    }
    for name in ("loki-operator", "cluster-logging"):
        subscription = subscriptions[name]
        assert subscription["spec"]["channel"] == "stable-6.6"
        assert subscription["spec"]["source"] == "redhat-operators"
        assert subscription["spec"]["sourceNamespace"] == "openshift-marketplace"
        assert subscription["spec"]["installPlanApproval"] == "Automatic"

    assert subscriptions["loki-operator"]["metadata"]["namespace"] == (
        "openshift-operators-redhat"
    )
    assert subscriptions["cluster-logging"]["metadata"]["namespace"] == (
        "openshift-logging"
    )
    observability = subscriptions["cluster-observability-operator"]
    assert observability["metadata"]["namespace"] == "openshift-operators"
    assert observability["spec"] == {
        "channel": "stable",
        "installPlanApproval": "Automatic",
        "name": "cluster-observability-operator",
        "source": "redhat-operators",
        "sourceNamespace": "openshift-marketplace",
    }


def test_operator_manifest_contains_no_secret_values():
    rendered = OPERATORS.read_text()
    for forbidden in ("access_key", "secret_key", "password", "stringData:"):
        assert forbidden not in rendered


def test_one_seat_logging_pilot_is_application_only_and_explicitly_non_scale():
    documents = _documents(PILOT)
    resources = {
        (document["kind"], document["metadata"]["name"]): document
        for document in documents
    }

    loki = resources[("LokiStack", "logging-loki")]
    assert loki["spec"]["size"] == "1x.demo"
    assert loki["spec"]["storageClassName"] == "launchpad-nfs-ephemeral"
    assert loki["spec"]["storage"]["secret"] == {
        "name": "logging-loki-s3",
        "type": "s3",
    }
    assert loki["spec"]["tenants"]["mode"] == "openshift-logging"

    minio_pvc = resources[("PersistentVolumeClaim", "logging-minio")]
    assert minio_pvc["spec"]["storageClassName"] == "launchpad-nfs-ephemeral"
    assert minio_pvc["spec"]["resources"]["requests"]["storage"] == "100Gi"

    bootstrap = resources[("Job", "logging-minio-bootstrap")]
    bootstrap_command = bootstrap["spec"]["template"]["spec"]["containers"][0]["args"][0]
    assert "mc --config-dir /tmp/.mc alias set" in bootstrap_command
    assert "mc --config-dir /tmp/.mc mb --ignore-existing" in bootstrap_command

    forwarder = resources[("ClusterLogForwarder", "instance")]
    assert forwarder["spec"]["inputs"] == [
        {
            "name": "launchpad-application",
            "type": "application",
            "application": {"includes": [{"namespace": "launchpad-*"}]},
        }
    ]
    assert forwarder["spec"]["pipelines"] == [
        {
            "name": "application-logs",
            "inputRefs": ["launchpad-application"],
            "outputRefs": ["lokistack-out"],
        }
    ]
    assert forwarder["spec"]["outputs"][0]["tls"]["ca"] == {
        "key": "service-ca.crt",
        "configMapName": "logging-loki-gateway-ca-bundle",
    }

    bindings = {
        document["roleRef"]["name"]
        for document in documents
        if document["kind"] == "ClusterRoleBinding"
    }
    assert bindings == {"logging-collector-logs-writer", "collect-application-logs"}

    plugin = resources[("UIPlugin", "logging")]
    assert plugin["spec"]["type"] == "Logging"
    assert plugin["spec"]["logging"]["schema"] == "viaq"


def test_logging_pilot_references_a_runtime_secret_but_contains_no_credentials():
    rendered = PILOT.read_text()
    assert "logging-loki-s3" in rendered
    assert "kind: Secret" not in rendered
    for forbidden in ("access_key_id:", "access_key_secret:", "MINIO_ROOT_PASSWORD:"):
        assert forbidden not in rendered
