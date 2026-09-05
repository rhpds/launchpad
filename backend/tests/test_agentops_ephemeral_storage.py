"""Cleanup contract for disposable AgentOps seat storage on Arena."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STORAGE_CLASS = ROOT / "deploy/multicluster/arena-launchpad-ephemeral-storageclass.yaml"
CATALOG = ROOT / "catalog/agentops-observability/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/agentops-observability.yaml"
VALUES = ROOT / "deploy/workloads/agentops-seat/values.yaml"


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
