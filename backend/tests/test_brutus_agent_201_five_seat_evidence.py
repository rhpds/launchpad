import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/brutus-agent-201-five-seat-2026-09-05.json"


def test_brutus_agent_201_five_seat_functional_gate_is_green_but_not_promoted():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "GREEN-live-five-seat-internal"
    assert evidence["cluster_ref"] == "brutus"
    assert evidence["promotion_eligible"] is False
    assert evidence["normal_placement_enabled_after_run"] is False
    assert evidence["capacity_preview"]["requested_seats"] == 5
    assert evidence["functional_validation"]["seats_ready"] == 5
    assert evidence["functional_validation"]["simultaneous_agent_calls_http_200"] == 5
    assert evidence["functional_validation"]["inference_errors"] == 0
    assert max(evidence["performance"]["functional_journey_seconds"]) < 80


def test_brutus_agent_201_five_seat_proves_isolation_and_zero_residue():
    evidence = json.loads(EVIDENCE.read_text())

    authorization = evidence["authorization"]
    assert authorization["terminal_current_project_matches_seat"] == 5
    assert authorization["terminal_own_namespace_edit_allowed"] == 5
    assert authorization["terminal_cross_seat_get_denied"] == 5
    assert authorization["terminal_list_nodes_denied"] == 5

    cleanup = evidence["cleanup"]
    assert cleanup["workshop_status"] == "completed"
    assert cleanup["reclaimed_sessions"] == 5
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_showroom_applications"] == 0
    assert cleanup["remaining_persistent_volumes"] == 0
    assert cleanup["active_pods_before_run"] == cleanup["active_pods_after_reclaim"]


def test_brutus_agent_201_five_seat_keeps_release_blockers_fail_closed():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["image_supply"]["durable_registry_result"] == "RED"
    assert evidence["route_tls"]["regression_tests"] == "GREEN-local"
    assert evidence["route_tls"]["live_rerun_required"] is True
    assert "twenty-five-seat workshop" in evidence["not_certified"]
    assert "Brutus public access" in evidence["not_certified"]
    assert evidence["contains_plaintext_credentials"] is False


def test_brutus_agent_201_five_seat_red_green_matrix_is_complete():
    evidence = json.loads(EVIDENCE.read_text())

    assert {row["id"] for row in evidence["red_green_matrix"]} == {
        "BRUTUS5-SCALE-001",
        "BRUTUS5-ISOLATION-001",
        "BRUTUS5-CLEANUP-001",
        "BRUTUS5-TLS-001",
        "BRUTUS5-IMAGE-001",
    }
    assert all(row["red"] and row["green"] for row in evidence["red_green_matrix"])
