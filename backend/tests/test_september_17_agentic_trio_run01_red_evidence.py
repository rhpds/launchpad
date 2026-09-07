"""Immutable contract for the first exact September agentic-trio rehearsal."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "evidence/september-17-agentic-trio-run01-red-2026-09-06.json"
)
CHECKSUM = EVIDENCE.with_suffix(".json.sha256")


def test_exact_trio_run01_records_the_failure_without_overclaiming():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/event-certification/v1"
    assert evidence["overall_status"] == "RED"
    assert evidence["cluster_id"] == "arena"
    assert evidence["provisioning"]["ready_seats"] == 75
    assert evidence["provisioning"]["failed_seats"] == 0
    assert evidence["participant_functional_probes"]["completed"] is False
    assert evidence["participant_functional_probes"]["route_failures"] == 2
    assert evidence["infrastructure_failure"]["node"] == "rhgnr1"
    assert evidence["infrastructure_failure"]["node_not_ready_observed"] is True
    assert evidence["infrastructure_failure"]["control_plane_interrupted"] is True
    assert evidence["cleanup"]["workshops_completed"] == 3
    assert evidence["cleanup"]["reclaimed_seats"] == 75
    assert evidence["cleanup"]["remaining_namespaces"] == 0
    assert evidence["cleanup"]["remaining_argocd_applications"] == 0
    assert evidence["rubric"]["score"] < evidence["rubric"]["required"]
    assert evidence["release_decision"] == "not-certified"


def test_exact_trio_run01_evidence_is_hash_verified():
    expected = CHECKSUM.read_text().split()[0]
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
