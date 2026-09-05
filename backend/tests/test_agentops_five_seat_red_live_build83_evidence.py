from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-five-seat-red-live-build83-2026-09-05.json"


def test_build83_five_seat_failure_is_preserved_as_red_live_evidence():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["cluster"] == "arena"
    assert evidence["outcome"] == {
        "seats_requested": 5,
        "persisted_sessions": 5,
        "seats_ready_before_failure": 2,
        "seats_started_after_reclaim_request": 1,
        "final_workshop_status": "completed",
        "final_seat_states": {"reclaimed": 5},
        "promotion_gate_passed": False,
    }
    assert {finding["id"] for finding in evidence["root_causes"]} == {
        "AGENTOPS-5-B83-RED-001",
        "AGENTOPS-5-B83-RED-002",
        "AGENTOPS-5-B83-RED-003",
    }


def test_build83_evidence_does_not_hide_cleanup_or_promotion_failure():
    evidence = json.loads(EVIDENCE.read_text())
    cleanup = evidence["cleanup"]

    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_argocd_applications"] == 0
    assert cleanup["remaining_persistent_volumes"] == 1
    assert cleanup["privilege_escalation_used"] is False
    assert cleanup["within_ten_minute_slo"] is False
    assert evidence["release_decision"]["catalog_max_workshop_seats"] == 1
    assert evidence["release_decision"]["five_seat_gate"] == "not certified"
    assert evidence["contains_plaintext_credentials"] is False


def test_build83_red_cells_have_tested_local_remediations():
    evidence = json.loads(EVIDENCE.read_text())
    matrix = {row["id"]: row for row in evidence["red_green_matrix"]}

    assert "agentops-certified=true" in matrix[
        "AGENTOPS-5-NODE-QUALIFICATION"
    ]["green_local"]
    assert "re-read persisted workshop state" in matrix[
        "AGENTOPS-5-QUEUED-RECLAIM"
    ]["green_local"]
    assert matrix["AGENTOPS-5-CLEANUP"]["green_live"] == "failed"
    assert evidence["test_evidence"]["applicable_regression_tests_passed"] == 1030
