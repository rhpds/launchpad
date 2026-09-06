"""Release contract for the reusable Multi-Agent five-seat proof run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "evidence/runs/multi-agent-quickstart-5-seat-multi-agent-5seat-20260906-01.json"
)


def test_multi_agent_five_seat_evidence_is_complete_and_green():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == (
        "launchpad.redhat.com/catalog-certification-evidence/v1"
    )
    assert evidence["catalog_item_id"] == "multi-agent-quickstart"
    assert evidence["result"] == "GREEN-live"
    assert evidence["errors"] == []
    assert evidence["plan"]["seats"] == 5
    assert evidence["plan"]["workshop_orders"] == 1
    assert evidence["plan"]["cluster_ref"] == "arena"
    assert evidence["plan"]["provision_concurrency"] == 2
    assert evidence["plan"]["probe_concurrency"] == 5

    assert len(evidence["seat_results"]) == 5
    assert {seat["seat_number"] for seat in evidence["seat_results"]} == set(
        range(1, 6)
    )
    for seat in evidence["seat_results"]:
        assert seat["cluster_ref"] == "arena"
        assert seat["probe"]["passed"] is True
        assert seat["probe"]["assertion_failures"] == []
        assert seat["probe"]["result"]["result"] == "GREEN-live-internal-seat"
        assert seat["probe"]["result"]["multi_agent_journey"]["steps"] == 3
        assert seat["probe"]["result"]["multi_agent_journey"]["errors"] == []
        assert "cross_namespace=DENIED" in seat["probe"]["result"][
            "terminal_scope"
        ]
        assert "node_list=DENIED" in seat["probe"]["result"]["terminal_scope"]
        assert seat["probe"]["result"]["contains_sensitive_values"] is False
        assert len(seat["showroom"]) == 4
        assert all(page["passed"] for page in seat["showroom"])

    assert all(value is True for value in evidence["gates"].values())
    assert set(evidence["validation_matrix"].values()) == {"GREEN-live"}
    assert evidence["rubric"]["score"] == 100
    assert evidence["rubric"]["passed"] is True
    assert evidence["rubric"]["categories"]["authorization"] == {
        "awarded": 15,
        "passed": True,
        "requires": [
            "namespace_isolation_passed",
            "sensitive_values_absent",
        ],
        "weight": 15,
    }
    assert evidence["promotion"] == {
        "consecutive_passing_runs": 1,
        "eligible": True,
        "required_consecutive_runs": 1,
    }
    assert evidence["cleanup"]["status"] == "completed"
    assert evidence["cleanup"]["model_keys_revoked"] is True
    assert all(
        count == 0 for count in evidence["cleanup"]["resource_counts"].values()
    )
    assert evidence["security"] == {
        "contains_plaintext_credentials": False,
        "credential_values_logged": False,
    }


def test_multi_agent_five_seat_evidence_checksum_is_valid():
    manifest = EVIDENCE.with_name(EVIDENCE.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
