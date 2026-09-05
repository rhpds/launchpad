"""Contracts for the Arena control-plane reliability guardrails."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / "deploy/launchpad/overlays/arena"


def _documents(name: str) -> list[dict]:
    return [
        document
        for document in yaml.safe_load_all((OVERLAY / name).read_text())
        if document
    ]


def test_arena_overlay_installs_reliability_resources():
    kustomization = yaml.safe_load((OVERLAY / "kustomization.yaml").read_text())
    assert "reliability.yaml" in kustomization["resources"]

    documents = _documents("reliability.yaml")
    rules = next(item for item in documents if item["kind"] == "PrometheusRule")
    alert_names = {
        rule["alert"]
        for group in rules["spec"]["groups"]
        for rule in group["rules"]
    }
    assert {
        "ArenaWorkerNotReady",
        "ArenaIngressRouterReplicaUnavailable",
        "LaunchpadControlPlaneUnavailable",
        "LaunchpadReconcilerFailed",
    } <= alert_names

    pdbs = [item for item in documents if item["kind"] == "PodDisruptionBudget"]
    assert {item["metadata"]["name"] for item in pdbs} == {
        "partner-portal",
        "launchpad-admin",
        "public-access-gateway",
    }
    assert all(item["spec"]["minAvailable"] == 1 for item in pdbs)


def test_arena_stateless_frontends_are_spread_across_workers():
    documents = _documents("patch-runtime.yaml")
    deployments = {
        item["metadata"]["name"]: item
        for item in documents
        if item["kind"] == "Deployment"
    }

    for name in ("partner-portal", "admin", "public-access-gateway"):
        deployment = deployments[name]
        assert deployment["spec"]["replicas"] == 2
        assert deployment["spec"]["strategy"] == {
            "type": "RollingUpdate",
            "rollingUpdate": {"maxUnavailable": 1, "maxSurge": 0},
        }
        constraints = deployment["spec"]["template"]["spec"][
            "topologySpreadConstraints"
        ]
        assert constraints == [
            {
                "maxSkew": 1,
                "topologyKey": "kubernetes.io/hostname",
                "whenUnsatisfiable": "DoNotSchedule",
                "labelSelector": {
                    "matchLabels": {"app.kubernetes.io/name": name}
                },
            }
        ]


def test_backend_single_replica_limit_is_explicit():
    documents = _documents("patch-runtime.yaml")
    backend = next(
        item
        for item in documents
        if item["kind"] == "Deployment" and item["metadata"]["name"] == "backend"
    )
    annotations = backend["metadata"]["annotations"]
    assert annotations["launchpad.redhat.com/ha-blocker"] == (
        "in-memory-session-cache-must-be-externalized-before-replicas-exceed-one"
    )


def test_cpu_model_readiness_does_not_flap_during_a_participant_burst():
    patch = yaml.safe_load(
        (OVERLAY / "operational-patches/ovms-granite-2b-readiness.yaml").read_text()
    )
    containers = {
        container["name"]: container
        for container in patch["spec"]["template"]["spec"]["containers"]
    }
    for name in ("ovms", "tls-proxy"):
        probe = containers[name]["readinessProbe"]
        assert probe["timeoutSeconds"] == 5
        assert probe["failureThreshold"] == 6

    driver = (ROOT / "scripts/apply-arena-model-readiness.sh").read_text()
    assert "*config-arena*" in driver
    assert "refusing to mutate a non-Arena cluster" in driver
    assert "ovms-granite-2b-readiness.yaml" in driver


def test_agent_model_has_two_replicas_for_concurrent_participant_use():
    resources = list(
        yaml.safe_load_all(
            (ROOT / "deploy/models/arena/granite-3.2-8b-tools.yaml").read_text()
        )
    )
    deployment = next(resource for resource in resources if resource["kind"] == "Deployment")

    assert deployment["spec"]["replicas"] == 2
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert "--max-num-seqs=64" in container["args"]
    assert container["readinessProbe"]["timeoutSeconds"] == 5
