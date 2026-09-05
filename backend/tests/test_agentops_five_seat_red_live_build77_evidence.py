from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-five-seat-red-live-build77-2026-09-05.json"


def test_build77_five_seat_failure_is_preserved_as_red_live_evidence():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-live"
    assert evidence["outcome"]["seats_requested"] == 5
    assert evidence["outcome"]["persisted_sessions"] == 4
    assert evidence["outcome"]["promotion_gate_passed"] is False
    assert evidence["capacity_and_staging"]["first_wave_namespaces"] == 4
    assert evidence["capacity_and_staging"]["fifth_namespace_created"] is False
    assert evidence["capacity_and_staging"]["rhgnr1_peak_active_pods"] == 239
    assert evidence["capacity_and_staging"]["worker_became_not_ready"] is True
    assert evidence["capacity_and_staging"]["postgresql_restarts_before_worker_outage"] == 0
    assert {finding["id"] for finding in evidence["root_causes"]} == {
        "AGENTOPS-5-B77-RED-001",
        "AGENTOPS-5-B77-RED-002",
    }
    assert evidence["cleanup"] == {
        "normal_group_reclaim_relinked_all_persisted_sessions": True,
        "direct_session_reclaims_required": 0,
        "force_deleted_stale_pod_records": 18,
        "orphan_argocd_hook_finalizers_removed": 2,
        "released_pvs_explicitly_deleted": 4,
        "remaining_namespaces": 0,
        "remaining_argocd_applications": 0,
        "remaining_persistent_volumes": 0,
        "within_ten_minute_slo": False,
    }
    assert evidence["release_decision"]["catalog_max_workshop_seats"] == 1
    assert evidence["contains_plaintext_credentials"] is False
