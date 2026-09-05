from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/fleet-placement-candidate-2026-09-05.json"


def test_fleet_candidate_preserves_headroom_and_fail_closed_targets():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["result"] == "RED-readiness"
    assert evidence["participant_contract"] == {
        "one_public_entrypoint": True,
        "one_instructor_code_per_order": True,
        "one_participant_identity": True,
        "cluster_ref_routes_private_origins": True,
        "quick_tunnel_is_event_ready": False,
    }
    clusters = evidence["clusters"]
    for cluster in clusters.values():
        expected = (
            cluster["schedulable_pod_slots"]
            - cluster["active_worker_pods"]
            - cluster["reserved_headroom_pods"]
        )
        assert cluster["additional_pods_after_headroom"] == expected

    assert clusters["brutus"]["additional_pods_after_headroom"] == 91
    assert clusters["oberon"]["additional_pods_after_headroom"] == 39
    assert clusters["brutus"]["enabled_for_launchpad"] is False
    assert clusters["oberon"]["enabled_for_launchpad"] is False
    brutus_certification = clusters["brutus"]["certification"]
    assert brutus_certification["one_seat"] == "GREEN-live"
    assert brutus_certification["five_seat"] == "GREEN-live-warm-functional"
    assert brutus_certification["twenty_five_seat"] == "not-run"
    assert brutus_certification["capacity_preview_seats"] == 22
    assert brutus_certification["own_namespace_edit"] is True
    assert brutus_certification["cross_namespace_edit"] is False
    assert brutus_certification["remaining_namespaces"] == 0
    assert brutus_certification["remaining_applications"] == 0
    assert brutus_certification["five_seat_provisioning_seconds"] == 48
    assert brutus_certification["five_seat_functional_p95_seconds"] < 80
    assert brutus_certification["five_seat_reclaim_seconds"] == 39
    assert brutus_certification["integrated_registry_storage"] == (
        "pvc:nfs-storage/launchpad-image-registry-storage"
    )
    assert brutus_certification["durable_registry_result"] == "GREEN-live"
    assert brutus_certification["promotion_eligible"] is False
    assert brutus_certification["public_access_certified"] is False
    assert evidence["candidate_assignment"] == {
        "agentops-observability": "arena",
        "intel-llm-cpu-serving": "oberon",
        "intel-xeon6-agent-201": "brutus",
    }
    assert evidence["release_decision"]["placement_enabled"] is False
    assert evidence["release_decision"]["brutus_status"] == (
        "five-seat-functional-disabled"
    )
    assert evidence["contains_plaintext_credentials"] is False
