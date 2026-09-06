"""Contract for the 25-seat run that exposed asynchronous residue timing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "evidence/runs/multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-02.json"
)


def test_all_participant_gates_passed_but_cleanup_snapshot_remained_red():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["errors"] == []
    assert evidence["plan"]["seats"] == 25
    assert evidence["order"]["status_before_reclaim"] == "ready"
    assert evidence["order"]["seat_count"] == 25
    assert len(evidence["seat_results"]) == 25
    assert all(seat["probe"]["passed"] for seat in evidence["seat_results"])
    assert all(
        len(seat["showroom"]) == 4
        and all(page["passed"] for page in seat["showroom"])
        for seat in evidence["seat_results"]
    )
    assert evidence["gates"]["all_seats_ready"] is True
    assert evidence["gates"]["seat_probes_passed"] is True
    assert evidence["gates"]["namespace_isolation_passed"] is True
    assert evidence["gates"]["cleanup_completed"] is True
    assert evidence["gates"]["model_keys_revoked"] is True
    assert evidence["gates"]["zero_residue_cleanup"] is False
    assert evidence["cleanup"]["resource_counts"]["namespaces"] == 20
    assert evidence["cleanup"]["resource_counts"]["secrets"] == 40
    assert evidence["rubric"]["score"] == 85
    assert evidence["promotion"]["eligible"] is False
    assert evidence["promotion"]["consecutive_passing_runs"] == 0
    assert evidence["security"]["contains_plaintext_credentials"] is False


def test_cleanup_red_evidence_checksum_is_valid():
    manifest = EVIDENCE.with_name(EVIDENCE.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
