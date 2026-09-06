"""Contract for the 25-seat run that exposed concurrent probe fragility."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "evidence/runs/multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-04.json"
)


def test_concurrent_probe_failure_is_red_and_cannot_count_for_promotion():
    evidence = json.loads(EVIDENCE.read_text())
    failed = [
        seat for seat in evidence["seat_results"] if not seat["probe"]["passed"]
    ]

    assert evidence["result"] == "RED-live"
    assert evidence["errors"] == []
    assert evidence["order"]["seat_count"] == 25
    assert evidence["order"]["status_before_reclaim"] == "ready"
    assert evidence["order"]["ready_seconds"] <= 2400
    assert len(evidence["seat_results"]) == 25
    assert [seat["seat_number"] for seat in failed] == [2, 3, 9]
    assert all(seat["probe"]["exit_code"] == 4 for seat in failed)
    assert sum(seat["probe"]["passed"] for seat in evidence["seat_results"]) == 22
    assert evidence["gates"]["showroom_pages_passed"] is True
    assert evidence["gates"]["seat_probes_passed"] is False
    assert evidence["gates"]["zero_residue_cleanup"] is True
    assert evidence["rubric"]["score"] == 60
    assert evidence["promotion"] == {
        "consecutive_passing_runs": 0,
        "eligible": False,
        "required_consecutive_runs": 3,
    }
    assert all(
        count == 0 for count in evidence["cleanup"]["resource_counts"].values()
    )
    assert evidence["security"]["contains_plaintext_credentials"] is False


def test_concurrent_probe_red_evidence_checksum_is_valid():
    manifest = EVIDENCE.with_name(EVIDENCE.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
