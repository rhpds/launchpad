"""Release contract for the post-hardening 25-seat promotion sequence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = [
    (
        "multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-05.json",
        1,
        False,
    ),
    (
        "multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-06.json",
        2,
        False,
    ),
    (
        "multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-07.json",
        3,
        True,
    ),
]


def test_post_hardening_twenty_five_seat_runs_are_consecutive_green():
    for filename, consecutive, eligible in RUNS:
        evidence_path = ROOT / "evidence/runs" / filename
        evidence = json.loads(evidence_path.read_text())

        assert evidence["result"] == "GREEN-live"
        assert evidence["errors"] == []
        assert evidence["contract"]["catalog_version"] == "0.2.2"
        assert evidence["plan"]["seats"] == 25
        assert evidence["plan"]["cluster_ref"] == "arena"
        assert evidence["plan"]["probe_concurrency"] == 10
        assert evidence["order"]["seat_count"] == 25
        assert evidence["order"]["status_before_reclaim"] == "ready"
        assert evidence["order"]["ready_seconds"] <= 2400
        assert len(evidence["seat_results"]) == 25
        assert all(seat["probe"]["passed"] for seat in evidence["seat_results"])
        assert all(
            len(seat["showroom"]) == 4
            and all(page["passed"] for page in seat["showroom"])
            for seat in evidence["seat_results"]
        )
        assert all(value is True for value in evidence["gates"].values())
        assert set(evidence["validation_matrix"].values()) == {"GREEN-live"}
        assert evidence["rubric"]["score"] == 100
        assert evidence["rubric"]["passed"] is True
        assert evidence["promotion"] == {
            "consecutive_passing_runs": consecutive,
            "eligible": eligible,
            "required_consecutive_runs": 3,
        }
        assert evidence["cleanup"]["seconds"] <= 1200
        assert all(
            count == 0
            for count in evidence["cleanup"]["resource_counts"].values()
        )
        assert evidence["security"]["contains_plaintext_credentials"] is False

        manifest = evidence_path.with_name(evidence_path.name + ".sha256")
        expected, manifest_filename = manifest.read_text().strip().split(
            "  ", maxsplit=1
        )
        assert manifest_filename == evidence_path.name
        assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == expected
