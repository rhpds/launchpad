"""Release contract for the first GREEN Multi-Agent 25-seat proof run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "evidence/runs/multi-agent-quickstart-25-seat-multi-agent-25seat-20260906-03.json"
)


def test_first_twenty_five_seat_green_run_is_complete():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == (
        "launchpad.redhat.com/catalog-certification-evidence/v1"
    )
    assert evidence["catalog_item_id"] == "multi-agent-quickstart"
    assert evidence["result"] == "GREEN-live"
    assert evidence["errors"] == []
    assert evidence["contract"]["catalog_version"] == "0.2.2"
    assert evidence["plan"]["seats"] == 25
    assert evidence["plan"]["workshop_orders"] == 1
    assert evidence["plan"]["cluster_ref"] == "arena"
    assert evidence["plan"]["provision_concurrency"] == 2
    assert evidence["plan"]["probe_concurrency"] == 10
    assert evidence["order"]["seat_count"] == 25
    assert evidence["order"]["cluster_ref"] == "arena"
    assert evidence["order"]["status_before_reclaim"] == "ready"
    assert evidence["order"]["ready_seconds"] <= 2400

    assert len(evidence["seat_results"]) == 25
    assert {seat["seat_number"] for seat in evidence["seat_results"]} == set(
        range(1, 26)
    )
    for seat in evidence["seat_results"]:
        assert seat["cluster_ref"] == "arena"
        assert seat["probe"]["passed"] is True
        assert seat["probe"]["assertion_failures"] == []
        result = seat["probe"]["result"]
        assert result["result"] == "GREEN-live-internal-seat"
        assert result["multi_agent_journey"]["steps"] == 3
        assert result["multi_agent_journey"]["errors"] == []
        assert "cross_namespace=DENIED" in result["terminal_scope"]
        assert "node_list=DENIED" in result["terminal_scope"]
        assert result["contains_sensitive_values"] is False
        assert len(seat["showroom"]) == 4
        assert all(page["passed"] for page in seat["showroom"])

    assert all(value is True for value in evidence["gates"].values())
    assert set(evidence["validation_matrix"].values()) == {"GREEN-live"}
    assert evidence["rubric"]["score"] == 100
    assert evidence["rubric"]["passed"] is True
    assert evidence["promotion"] == {
        "consecutive_passing_runs": 1,
        "eligible": False,
        "required_consecutive_runs": 3,
    }
    assert evidence["cleanup"]["status"] == "completed"
    assert evidence["cleanup"]["seconds"] <= 1200
    assert evidence["cleanup"]["model_keys_revoked"] is True
    assert all(
        count == 0 for count in evidence["cleanup"]["resource_counts"].values()
    )
    assert evidence["security"] == {
        "contains_plaintext_credentials": False,
        "credential_values_logged": False,
    }


def test_first_twenty_five_seat_green_evidence_checksum_is_valid():
    manifest = EVIDENCE.with_name(EVIDENCE.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
