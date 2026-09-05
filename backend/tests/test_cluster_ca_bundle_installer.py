from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/install-cluster-ca-bundle.sh"
ARENA_RUNTIME_PATCH = ROOT / "deploy/launchpad/overlays/arena/patch-runtime.yaml"


def test_cluster_ca_bundle_installer_uses_only_explicit_kubeconfigs():
    script = SCRIPT.read_text()

    assert script.count('oc --kubeconfig "$control_kubeconfig"') >= 5
    assert 'oc --kubeconfig "$kubeconfig"' in script
    assert "oc config use-context" not in script
    assert "OPENSHIFT_PASSWORD" not in script
    assert "insecure-skip-tls-verify" not in script


def test_cluster_ca_bundle_installer_enables_verified_python_clients():
    script = SCRIPT.read_text()

    assert "default-ingress-cert" in script
    assert "launchpad-cluster-ca-bundle" in script
    assert "SSL_CERT_FILE=/etc/launchpad-ca/ca-bundle.crt" in script
    assert "REQUESTS_CA_BUNDLE=/etc/launchpad-ca/ca-bundle.crt" in script


def test_arena_runtime_keeps_cluster_ca_bundle_mount_under_gitops():
    document = list(__import__("yaml").safe_load_all(ARENA_RUNTIME_PATCH.read_text()))[0]
    pod_spec = document["spec"]["template"]["spec"]
    container = pod_spec["containers"][0]
    env = {item["name"]: item["value"] for item in container["env"]}
    mounts = {item["name"]: item for item in container["volumeMounts"]}
    volumes = {item["name"]: item for item in pod_spec["volumes"]}

    assert env["SSL_CERT_FILE"] == "/etc/launchpad-ca/ca-bundle.crt"
    assert env["REQUESTS_CA_BUNDLE"] == "/etc/launchpad-ca/ca-bundle.crt"
    assert mounts["cluster-ca-bundle"]["mountPath"] == "/etc/launchpad-ca"
    assert volumes["cluster-ca-bundle"]["configMap"] == {
        "name": "launchpad-cluster-ca-bundle",
        "optional": True,
    }
