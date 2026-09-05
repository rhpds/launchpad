from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MODEL_ACCESS = ROOT / "deploy/multicluster/arena-remote-model-access.yaml"


def _documents(path: Path) -> list[dict]:
    return [item for item in yaml.safe_load_all(path.read_text()) if item]


def test_remote_tools_model_uses_private_arena_route_and_router_only_ingress():
    documents = _documents(MODEL_ACCESS)
    route = next(item for item in documents if item["kind"] == "Route")
    policy = next(item for item in documents if item["kind"] == "NetworkPolicy")

    assert route["metadata"]["namespace"] == "fleet-llm-d"
    assert route["metadata"]["labels"]["launchpad.redhat.com/exposure"] == "private"
    assert route["metadata"]["annotations"] == {
        "haproxy.router.openshift.io/timeout": "300s"
    }
    assert route["spec"]["to"] == {
        "kind": "Service",
        "name": "vllm-granite-3-2-8b-tools",
    }
    assert route["spec"]["port"]["targetPort"] == "http"
    assert route["spec"]["tls"] == {
        "termination": "edge",
        "insecureEdgeTerminationPolicy": "Redirect",
    }

    ingress = policy["spec"]["ingress"]
    assert ingress == [
        {
            "from": [
                {
                    "namespaceSelector": {
                        "matchLabels": {
                            "network.openshift.io/policy-group": "ingress"
                        }
                    }
                }
            ],
            "ports": [{"protocol": "TCP", "port": 8080}],
        }
    ]


def test_brutus_registers_only_the_certified_remote_tools_model():
    config = yaml.safe_load((ROOT / "config/clusters.yaml").read_text())
    brutus = next(
        item for item in config["clusters"] if item["cluster_id"] == "brutus"
    )

    assert brutus["enabled"] is False
    assert "model_endpoint" in brutus["capabilities"]
    assert brutus["model_endpoints"] == {
        "granite-3.2-8b-tools": (
            "https://vllm-granite-3-2-8b-tools-fleet-llm-d."
            "apps.arena.fm2aihpcsed.com/v1"
        )
    }
