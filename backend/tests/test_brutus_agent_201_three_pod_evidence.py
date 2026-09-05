from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/brutus-agent-201-three-pod-certification-2026-09-05.json"
CHECKSUM = ROOT / "evidence/brutus-agent-201-three-pod-certification-2026-09-05.json.sha256"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_three_pod_agent_201_reaches_the_internal_twenty_five_seat_gate():
    evidence = _evidence()

    assert evidence["result"] == "GREEN-live-internal-25"
    assert evidence["cluster_ref"] == "brutus"
    assert evidence["catalog_contract"] == {
        "catalog_item_id": "intel-xeon6-agent-201",
        "seat_cpu_millicores": 415,
        "seat_memory_mib": 912,
        "seat_pods": 3,
        "max_workshop_seats": 25,
    }
    run = evidence["runs"]["twenty_five_seat"]
    assert run["seats_ready"] == 25
    assert run["pods"] == 75
    assert run["running_pods"] == 75
    assert run["ready_containers"] == run["containers"] == 150
    assert run["container_restarts"] == 0
    assert run["argocd_synced_healthy"] == 25
    assert run["functional_http_200"] == 25
    assert run["inference_errors"] == 0
    assert len(run["functional_journey_seconds"]) == 25
    assert max(run["functional_journey_seconds"]) < 80


def test_twenty_five_seats_preserve_isolation_headroom_and_zero_residue():
    evidence = _evidence()
    run = evidence["runs"]["twenty_five_seat"]

    assert run["terminal_project_matches_seat"] == 25
    assert run["own_namespace_edit_allowed"] == 25
    assert run["cross_namespace_read_denied"] == 25
    assert run["node_list_denied"] == 25
    assert run["node_pressure"] == {
        "memory": False,
        "disk": False,
        "pid": False,
    }
    assert run["active_cluster_pods_at_peak"] == 184
    assert run["protected_pod_ceiling"] == 200
    assert run["cleanup"]["remaining_namespaces"] == 0
    assert run["cleanup"]["remaining_persistent_volumes"] == 0
    assert run["cleanup"]["remaining_argocd_applications"] == 0
    assert run["cleanup"]["active_cluster_pods_after_reclaim"] == 109


def test_exact_corrected_content_received_a_rendered_live_regression():
    evidence = _evidence()
    regression = evidence["corrected_content_regression"]

    assert regression["catalog_version"] == "1.0.2"
    assert regression["showroom_content_ref"] == (
        "946175fde859e791568b95f1181833d92c448e8a"
    )
    assert regression["showroom_content_tag"] == "intel-guided-content-v1.0.13"
    assert regression["module_02_http_status"] == 200
    assert regression["rendered_two_workload_pods"] is True
    assert regression["rendered_inspect_deployed_agent"] is True
    assert regression["browser_errors"] == 0
    assert regression["functional_http_status"] == 200
    assert regression["cleanup"]["remaining_namespaces"] == 0
    assert regression["cleanup"]["remaining_persistent_volumes"] == 0
    assert regression["cleanup"]["remaining_argocd_applications"] == 0


def test_evidence_keeps_internal_certification_distinct_from_ga_and_public_access():
    evidence = _evidence()

    assert evidence["image_supply"]["durable_registry_result"] == "GREEN-live"
    assert evidence["route_tls"]["verified_live_rerun"] is True
    assert evidence["normal_placement_enabled_after_run"] is False
    assert evidence["release_boundary"] == {
        "internal_twenty_five_seat_scale_gate": True,
        "public_access_certified": False,
        "openshift_console_oidc_certified": False,
        "sixty_minute_soak_complete": False,
        "consecutive_twenty_five_seat_runs": 1,
        "general_availability": False,
    }
    assert evidence["contains_plaintext_credentials"] is False


def test_three_pod_certification_evidence_checksum_matches_artifact():
    expected, filename = CHECKSUM.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
