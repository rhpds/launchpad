"""Release contract for the v0.2.5 hands-on 25-seat regression."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "evidence/runs/"
    "multi-agent-quickstart-25-seat-multi-agent-v025-25seat-20260906-01.json"
)


def test_v025_hands_on_twenty_five_seat_regression_is_green():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == (
        "launchpad.redhat.com/catalog-certification-evidence/v1"
    )
    assert evidence["catalog_item_id"] == "multi-agent-quickstart"
    assert evidence["contract"]["catalog_version"] == "0.2.5"
    assert evidence["result"] == "GREEN-live"
    assert evidence["errors"] == []
    assert evidence["plan"]["seats"] == 25
    assert evidence["plan"]["cluster_ref"] == "arena"
    assert evidence["plan"]["probe_concurrency"] == 10
    assert evidence["order"]["seat_count"] == 25
    assert evidence["order"]["status_before_reclaim"] == "ready"
    assert evidence["order"]["ready_seconds"] <= 2400

    assert len(evidence["seat_results"]) == 25
    assert {seat["seat_number"] for seat in evidence["seat_results"]} == set(
        range(1, 26)
    )
    for seat in evidence["seat_results"]:
        probe = seat["probe"]
        result = probe["result"]

        assert seat["cluster_ref"] == "arena"
        assert probe["passed"] is True
        assert probe["assertion_failures"] == []
        assert result["learner_policy"] == {
            "applied_max_tokens": 48,
            "configmap_removed": True,
            "rollback_restored_baseline": True,
            "workflow_passed": True,
        }
        assert result["participant_ui_journey"] == {
            "executor_present": True,
            "http_error": False,
            "step_count_one": True,
        }
        assert result["multi_agent_journey"]["agents"] == [
            "research",
            "analyst",
            "executor",
        ]
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


def test_v025_hands_on_twenty_five_seat_evidence_checksum_is_valid():
    manifest = EVIDENCE.with_name(EVIDENCE.name + ".sha256")
    expected, filename = manifest.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
