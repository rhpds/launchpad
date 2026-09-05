from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/migrate-image-registry-to-persistent-nfs.sh"


def test_registry_migration_is_explicit_and_preserves_existing_blobs():
    script = SCRIPT.read_text()

    assert ': "${KUBECONFIG:' in script
    assert 'storageClassName: "$storage_class"' in script
    assert "ReadWriteMany" in script
    assert "image-registry-storage-migrate" in script
    assert '"networkpolicy/$migration_policy"' in script
    assert "tar -C /registry -cf - ." in script
    assert "--no-same-owner" in script
    assert "--no-same-permissions" in script
    assert "--no-overwrite-dir" in script
    assert "--touch -C /target -xf -" in script
    assert "socat -u TCP-LISTEN:18080" in script
    assert "socat -u STDIN" in script
    assert "status.podIP" in script
    assert "kind: NetworkPolicy" in script
    assert '\"emptyDir\":null' in script
    assert '\"pvc\":{\"claim\":\"' in script
    assert "oc config use-context" not in script
    assert "insecure-skip-tls-verify" not in script


def test_registry_migration_verifies_operator_and_forces_persistence_restart():
    script = SCRIPT.read_text()

    assert "configs.imageregistry.operator.openshift.io cluster" in script
    assert "deployment/image-registry" in script
    assert "rollout restart" in script
    assert "rollout status" in script
    assert "Available" in script
    assert "Degraded" in script
