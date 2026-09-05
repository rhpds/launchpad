import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/brutus-persistent-registry-2026-09-05.json"
CHECKSUM = ROOT / "evidence/brutus-persistent-registry-2026-09-05.json.sha256"


def _evidence():
    return json.loads(EVIDENCE.read_text())


def test_brutus_registry_is_persistent_and_healthy_after_restart():
    evidence = _evidence()

    assert evidence["result"] == "GREEN-live"
    assert evidence["cluster_ref"] == "brutus"
    assert evidence["normal_placement_enabled_after_change"] is False
    assert evidence["storage"] == {
        "claim": "launchpad-image-registry-storage",
        "storage_class": "nfs-storage",
        "capacity": "100Gi",
        "status": "Bound",
        "access_mode": "ReadWriteMany",
        "persistent_volume_reclaim_policy": "Retain",
    }
    assert evidence["operator_conditions"] == {
        "Available": True,
        "Progressing": False,
        "Degraded": False,
    }
    assert evidence["persistence_proof"]["post_switch_restart_observed"] is True
    assert evidence["persistence_proof"]["registry_file_count"] == 170


def test_brutus_registry_serves_every_pinned_digest_after_restart():
    evidence = _evidence()
    probes = evidence["digest_pull_probes"]

    assert probes["image_pull_policy"] == "Always"
    assert len(probes["results"]) == 3
    assert all(result["phase"] == "Succeeded" for result in probes["results"])
    assert all(result["output"] == "pull-ok" for result in probes["results"])
    assert all(
        result["resolved_image_id"].endswith(result["expected_digest"])
        for result in probes["results"]
    )


def test_brutus_registry_migration_is_clean_and_keeps_placement_fail_closed():
    evidence = _evidence()

    assert evidence["cleanup"] == {
        "migration_pods_remaining": 0,
        "migration_network_policies_remaining": 0,
        "digest_probe_pods_remaining": 0,
    }
    assert {row["id"] for row in evidence["red_green_matrix"]} == {
        "BRUTUS-REGISTRY-STORAGE-001",
        "BRUTUS-REGISTRY-DIGEST-001",
        "BRUTUS-REGISTRY-CLEANUP-001",
    }
    assert all(row["red"] and row["green"] for row in evidence["red_green_matrix"])
    assert evidence["contains_plaintext_credentials"] is False


def test_brutus_registry_evidence_checksum_matches_artifact():
    expected, filename = CHECKSUM.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
