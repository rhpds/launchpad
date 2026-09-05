from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "evidence/agentops-five-seat-functional-live-build84-2026-09-05.json"
)


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_build84_five_seat_functional_boundary_is_green():
    evidence = _evidence()
    provisioning = evidence["provisioning"]
    participant = evidence["participant_validation"]
    journeys = evidence["concurrent_agent_journeys"]

    assert evidence["outcome"] == "pass"
    assert evidence["cluster"] == "arena"
    assert evidence["seat_count"] == 5
    assert provisioning["all_seats_ready"] is True
    assert provisioning["unique_session_count"] == 5
    assert provisioning["unique_namespace_count"] == 5
    assert provisioning["selected_nodes"] == ["gnr2.fm2aihpcsed.com"]
    assert provisioning["steady_pods"] == 65
    assert provisioning["not_ready_pods"] == 0
    assert provisioning["container_restarts"] == 0
    assert provisioning["healthy_synced_argocd_applications"] == 10
    assert participant["showroom_pages_http_200"] == 55
    assert participant["default_project_matches_seat"] == 5
    assert participant["own_namespace_edit_allowed"] == 5
    assert participant["cross_namespace_read_denied"] == 5
    assert participant["embedded_chunks"] == 205
    assert participant["mlflow_ok_traces"] == 5
    assert journeys["successful_journeys"] == 5
    assert journeys["grounded_answers"] == 5


def test_build84_normal_and_fault_reclaim_are_zero_residue():
    evidence = _evidence()
    cleanup = evidence["normal_cleanup"]
    fault = evidence["queued_reclaim_fault"]

    assert cleanup["all_seats_reclaimed"] is True
    assert cleanup["completed_seconds"] <= 600
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_applications"] == 0
    assert cleanup["remaining_persistent_volumes"] == 0
    assert cleanup["manual_cleanup_required"] is False
    assert fault["maximum_namespaces_observed"] == 2
    assert fault["maximum_sessions_observed"] == 2
    assert fault["queued_seats_without_sessions"] == 3
    assert fault["queued_seat_cancellation_contract_passed"] is True
    assert fault["final_cleanup_verified"] is True
    assert fault["cleanup_seconds"] <= 600
    assert fault["final_state"]["reclaimed_seats"] == 5
    assert fault["final_state"]["seats_with_sessions"] == 2
    assert fault["final_state"]["queued_seats_reclaimed_without_sessions"] == 3
    assert fault["final_state"]["namespaces"] == 0
    assert fault["final_state"]["applications"] == 0
    assert fault["final_state"]["persistent_volumes"] == 0
    assert evidence["gate_rubric"]["score"] == 100
    assert evidence["gate_rubric"]["required"] == 100


def test_build84_evidence_promotes_only_the_proven_internal_boundary():
    evidence = _evidence()

    assert evidence["release_decision"]["catalog_max_workshop_seats"] == 5
    assert evidence["release_decision"]["five_seat_functional_gate"] == "passed"
    assert evidence["release_decision"]["five_seat_release_gate"] == "passed"
    assert evidence["public_access_certified"] is False
    assert evidence["twenty_five_seat_certified"] is False
    assert evidence["contains_plaintext_credentials"] is False
