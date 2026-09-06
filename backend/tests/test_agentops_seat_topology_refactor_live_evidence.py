from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-seat-topology-refactor-live-2026-09-05.json"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_agentops_refactor_capacity_contract_is_bounded_and_fail_closed():
    evidence = _evidence()
    capacity = evidence["capacity_contract"]

    assert capacity["steady_per_seat"]["pods"] == 12
    assert capacity["provisioning_concurrency"] == 2
    assert capacity["five_seat_estimated_pods"] == 68
    assert capacity["five_seat_steady_pods"] == 60
    assert capacity["twenty_five_seat_estimated_pods"] == 308
    assert capacity["live_max_seats"] == 11
    assert capacity["twenty_five_seat_admission"] == "rejected_before_mutation"


def test_agentops_refactor_five_seat_functional_and_recovery_gate_is_green():
    evidence = _evidence()
    gate = evidence["five_seat_gate"]
    recovery = evidence["fault_injection_and_recovery"]

    assert gate["collective_status"] == "ready"
    assert gate["unique_ready_seats"] == 5
    assert gate["active_pods"] == gate["ready_active_pods"] == 60
    assert gate["container_restarts"] == 0
    assert gate["healthy_synced_argocd_applications"] == 10
    assert gate["dspa_ready"] == 5
    assert gate["session_validation_failures"] == 0
    assert gate["participant_routes_http_200"] == gate["participant_routes_expected"]
    assert gate["showroom_pages_http_200"] == gate["showroom_pages_expected"]
    assert gate["terminal_default_project_matches_seat"] == 5
    assert gate["terminal_own_namespace_edit_allowed"] == 5
    assert gate["terminal_cross_seat_read_denied"] == 5
    assert gate["concurrent_agent_journeys"]["terminal_done"] == 5
    assert recovery["ready_seats_preserved"] == 2


def test_agentops_refactor_cleanup_is_zero_residue_without_scale_overclaim():
    evidence = _evidence()
    cleanup = evidence["cleanup"]
    decision = evidence["release_decision"]

    assert cleanup["final_status_after_build_92_retry"] == "completed"
    assert cleanup["failed_reclaims"] == 0
    assert cleanup["seat_statuses_reclaimed"] == 5
    assert cleanup["historical_retry_sessions_reclaimed"] == 8
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_applications"] == 0
    assert cleanup["remaining_persistent_volumes_by_label"] == 0
    assert cleanup["remaining_persistent_volumes_by_claim_namespace"] == 0
    assert cleanup["credentials_scrubbed"] is True
    assert evidence["contains_plaintext_credentials"] is False
    assert evidence["gate_rubric"]["score"] == 100
    assert decision["internal_five_seat"] == "GREEN"
    assert decision["catalog_max_seats"] == 5
    assert decision["twenty_five_seat"] == "BLOCKED_CAPACITY"
    assert decision["public_access"] == "NOT_IN_SCOPE"
