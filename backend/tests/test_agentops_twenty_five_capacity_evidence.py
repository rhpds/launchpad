from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-twenty-five-seat-capacity-red-2026-09-05.json"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_agentops_twenty_five_seat_gate_records_the_exact_capacity_gap():
    evidence = _evidence()

    assert evidence["outcome"] == "blocked-by-qualified-worker-capacity"
    assert evidence["requested_certification_seats"] == 25
    assert evidence["requested_resources"] == {
        "cpu_millicores": 62500,
        "memory_mib": 179200,
        "pod_slots": 425,
        "storage_gib_minimum": 750,
        "capacity_headroom_percent": 20,
    }
    assert evidence["live_preview"]["can_provision"] is False
    assert evidence["live_preview"]["supported_seats"] == 9
    assert evidence["live_preview"]["eligible_nodes"] == 1
    assert evidence["capacity_gap"]["seat_shortage"] == 16
    assert evidence["capacity_gap"]["additional_250_pod_workers_required"] == 2


def test_agentops_twenty_five_preview_failed_before_resource_creation():
    preview = _evidence()["live_preview"]

    assert preview["workshops_before"] == preview["workshops_after"]
    assert preview["sessions_before"] == preview["sessions_after"]
    assert preview["agentops_namespaces_before"] == 0
    assert preview["agentops_namespaces_after"] == 0


def test_agentops_capacity_control_is_green_without_overclaiming_release():
    evidence = _evidence()
    inventory = evidence["arena_inventory"]
    decision = evidence["release_decision"]

    assert inventory["platform"] == "BareMetal"
    assert inventory["baremetal_hosts_available"] == 0
    assert inventory["qualified_agentops_workers"] == ["gnr2.fm2aihpcsed.com"]
    assert decision["capacity_safety_gate"] == "passed"
    assert decision["twenty_five_seat_release_gate"] == "blocked"
    assert decision["eligible_existing_twenty_five_seat_clusters"] == []
    assert decision["catalog_max_workshop_seats"] == 5
    assert evidence["public_access_certified"] is False
    assert evidence["contains_plaintext_credentials"] is False


def test_no_other_registered_cluster_can_host_twenty_five_agentops_seats():
    clusters = _evidence()["other_registered_clusters"]

    assert set(clusters) == {"oberon", "brutus"}
    assert all(not cluster["agentops_capability_eligible"] for cluster in clusters.values())
    assert all(not cluster["twenty_five_seat_fit"] for cluster in clusters.values())
    assert clusters["oberon"]["empty_cluster_protected_pod_ceiling"] == 400
    assert clusters["brutus"]["empty_cluster_protected_pod_ceiling"] == 200
