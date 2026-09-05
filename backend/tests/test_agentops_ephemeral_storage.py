"""Cleanup contract for disposable AgentOps seat storage on Arena."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STORAGE_CLASS = ROOT / "deploy/multicluster/arena-launchpad-ephemeral-storageclass.yaml"
CATALOG = ROOT / "catalog/agentops-observability/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/agentops-observability.yaml"
VALUES = ROOT / "deploy/workloads/agentops-seat/values.yaml"
CLUSTER_REGISTRIES = (
    ROOT / "config/clusters.yaml",
    ROOT / "config/clusters-arena-cert.yaml",
    ROOT / "deploy/launchpad/overlays/arena/arena-clusters.yaml",
)


def test_arena_launchpad_storage_class_deletes_pvs_and_nfs_directories():
    storage_class = yaml.safe_load(STORAGE_CLASS.read_text())

    assert storage_class["kind"] == "StorageClass"
    assert storage_class["metadata"]["name"] == "launchpad-nfs-ephemeral"
    assert storage_class["provisioner"] == "cluster.local/nfs-subdir-external-provisioner"
    assert storage_class["reclaimPolicy"] == "Delete"
    assert storage_class["parameters"]["archiveOnDelete"] == "false"
    assert storage_class["allowVolumeExpansion"] is True


def test_agentops_uses_only_the_cleanup_certified_storage_class():
    catalog = yaml.safe_load(CATALOG.read_text())
    intake = yaml.safe_load(INTAKE.read_text())
    values = yaml.safe_load(VALUES.read_text())

    expected = "launchpad-nfs-ephemeral"
    assert values["storageClass"] == expected
    assert catalog["metadata"]["workload_helm_values"]["storageClass"] == expected
    assert intake["runtime"]["workload"]["helm_values"]["storageClass"] == expected


def test_arena_showroom_uses_cleanup_certified_ephemeral_storage_class():
    for registry_path in CLUSTER_REGISTRIES:
        registry = yaml.safe_load(registry_path.read_text())
        if registry.get("kind") == "ConfigMap":
            registry = yaml.safe_load(registry["data"]["clusters.yaml"])
        arena = next(
            cluster for cluster in registry["clusters"] if cluster["cluster_id"] == "arena"
        )
        assert arena["storage_class"] == "launchpad-nfs-ephemeral"
