import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/brutus-agent-201-one-seat-2026-09-05.json"


def test_brutus_agent_201_one_seat_is_green_but_not_promoted():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "GREEN-live-one-seat"
    assert evidence["cluster_ref"] == "brutus"
    assert evidence["capacity_preview"]["safe_seats"] == 22
    assert evidence["normal_placement_enabled_after_run"] is False
    assert evidence["functional_validation"]["inference_errors"] == 0
    assert set(evidence["functional_validation"]["required_tools"]) == {
        "intel_hardware_lookup",
        "openshift_capabilities",
        "reference_architectures",
    }
    assert "five-seat workshop" in evidence["not_certified"]
    assert "twenty-five-seat workshop" in evidence["not_certified"]
    assert "Brutus public access" in evidence["not_certified"]


def test_brutus_agent_201_one_seat_proves_isolation_and_zero_residue():
    evidence = json.loads(EVIDENCE.read_text())

    authorization = evidence["authorization"]
    assert authorization["participant_own_namespace_edit"] is True
    assert authorization["participant_default_namespace_edit"] is False
    assert authorization["participant_list_nodes"] is False
    assert authorization["terminal_own_namespace_edit"] is True
    assert authorization["terminal_default_namespace_edit"] is False

    cleanup = evidence["cleanup"]
    assert cleanup["workshop_status"] == "completed"
    assert cleanup["seat_status"] == "reclaimed"
    assert cleanup["all_retry_sessions_status"] == "reclaimed"
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_showroom_applications"] == 0
    assert cleanup["remaining_workload_applications"] == 0
    assert evidence["contains_plaintext_credentials"] is False


def test_brutus_agent_201_red_green_matrix_records_every_live_defect():
    evidence = json.loads(EVIDENCE.read_text())

    assert {row["id"] for row in evidence["red_green_matrix"]} == {
        "BRUTUS-CA-001",
        "BRUTUS-RBAC-001",
        "BRUTUS-IMAGE-001",
        "BRUTUS-RETRY-001",
        "BRUTUS-MODEL-001",
    }
    assert all(row["red"] and row["green"] for row in evidence["red_green_matrix"])
