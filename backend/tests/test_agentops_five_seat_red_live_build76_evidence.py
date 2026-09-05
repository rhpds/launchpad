from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-five-seat-red-live-build76-2026-09-05.json"


def test_build76_five_seat_failure_is_preserved_as_red_live_evidence():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["outcome"]["seats_requested"] == 5
    assert evidence["outcome"]["seats_ready_before_reclaim"] == 1
    assert evidence["outcome"]["seats_failed"] == 4
    assert evidence["outcome"]["promotion_gate_passed"] is False
    assert evidence["capacity_and_staging"]["corrected_reported_capacity_seats"] == 10
    assert evidence["capacity_and_staging"]["first_wave_namespaces"] == 4
    assert evidence["capacity_and_staging"]["rhgnr1_peak_active_pods"] == 243
    assert evidence["capacity_and_staging"]["worker_became_not_ready"] is False
    assert {finding["id"] for finding in evidence["root_causes"]} == {
        "AGENTOPS-5-B76-RED-001",
        "AGENTOPS-5-B76-RED-002",
    }
    assert evidence["cleanup"] == {
        "normal_group_reclaim_reclaimed_all_persisted_sessions": False,
        "direct_session_reclaims_required": 4,
        "remaining_namespaces": 0,
        "remaining_argocd_applications": 0,
        "remaining_persistent_volumes": 0,
        "within_ten_minute_slo": False,
    }
    assert evidence["release_decision"]["catalog_max_workshop_seats"] == 1
    assert evidence["test_evidence"]["applicable_regression_tests_passed"] == 988
    assert evidence["contains_plaintext_credentials"] is False
