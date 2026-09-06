"""Contract for the first Multi-Agent 25-seat RED infrastructure run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = (
    ROOT
    / "evidence/runs/multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-01.json"
)
FAULT = RUN.with_name(
    "multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-01-fault.json"
)


def _checksum_matches(path: Path) -> None:
    manifest = path.with_name(path.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == path.name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_interrupted_run_is_red_and_cannot_count_for_promotion():
    evidence = json.loads(RUN.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["plan"]["seats"] == 25
    assert evidence["plan"]["cluster_ref"] == "arena"
    assert evidence["order"]["workshop_id"] == (
        "29d49664-e1d5-487c-b083-a58a08664a7c"
    )
    assert any("ConnectionError" in error for error in evidence["errors"])
    assert evidence["promotion"]["eligible"] is False
    assert evidence["promotion"]["consecutive_passing_runs"] == 0
    assert evidence["rubric"]["score"] < 100
    assert evidence["security"]["contains_plaintext_credentials"] is False
    _checksum_matches(RUN)


def test_fault_record_proves_recovery_cleanup_and_remaining_ha_gaps():
    fault = json.loads(FAULT.read_text())

    assert fault["schema"] == (
        "launchpad.redhat.com/catalog-certification-fault-evidence/v1"
    )
    assert fault["result"] == "RED-live-infrastructure"
    assert fault["promotion_counted"] is False
    assert fault["failure"]["node"] == "rhgnr1"
    assert fault["failure"]["backend_route_http_status"] == 503
    assert fault["failure"]["ready_seats_before_interruption"] == 24
    assert fault["recovery"]["kueue_visibility_apis_available"] is True
    assert all(count == 0 for count in fault["recovery"]["resource_counts"].values())
    assert fault["remaining_risks"] == {
        "backend_replicas": 1,
        "image_registry_replicas": 1,
        "image_registry_storage": "EmptyDir",
        "kueue_anti_affinity": "preferred-not-required",
    }
    assert fault["security"]["contains_plaintext_credentials"] is False
    _checksum_matches(FAULT)
