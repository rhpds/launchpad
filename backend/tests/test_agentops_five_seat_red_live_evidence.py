from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-five-seat-red-live-2026-09-05.json"


def test_failed_agentops_five_seat_run_is_preserved_as_red_live_evidence():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["outcome"] == {
        "seats_requested": 5,
        "seats_ready": 0,
        "seats_failed": 5,
        "workshop_status_after_provisioning": "failed",
        "workshop_status_after_reclaim": "completed",
        "promotion_gate_passed": False,
    }
    assert evidence["observations"]["reported_capacity_was_valid"] is False
    assert evidence["observations"]["rhgnr1_peak_active_pods"] == 250
    assert evidence["observations"]["rhgnr1_became_not_ready"] is True
    assert len(evidence["root_causes"]) == 4
    assert all(
        row["green_live"] == "pending rerun"
        for row in evidence["red_green_matrix"]
    )
    assert evidence["cleanup"]["remaining_namespaces"] == 0
    assert evidence["cleanup"]["remaining_argocd_applications"] == 0
    assert evidence["cleanup"]["remaining_persistent_volumes"] == 0
    assert evidence["cleanup"]["remaining_temporary_cleanup_pods"] == 0
    assert evidence["cleanup"]["within_ten_minute_slo"] is False
    assert evidence["release_decision"]["catalog_max_workshop_seats"] == 1
    assert evidence["test_evidence"]["applicable_regression_tests_passed"] == 986
    assert evidence["contains_plaintext_credentials"] is False
