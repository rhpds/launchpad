"""Contract for the integrated Launchpad-created AgentOps seat evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-launchpad-one-seat-2026-09-05.json"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_launchpad_agentops_seat_waited_for_operator_readiness_and_completed():
    evidence = _evidence()

    assert evidence["schema"] == "launchpad.redhat.com/agentops-live-seat-evidence/v5"
    assert evidence["evidence_id"] == "LIVE-AGENTOPS-020"
    assert evidence["cluster_id"] == "arena"
    assert evidence["result"] == "pass-internal-one-seat"
    assert evidence["order"]["seat_count"] == 1
    assert evidence["order"]["cluster_ref_persisted"] is True
    gate = evidence["readiness_gate"]
    assert gate["observed_while_false"] == {
        "dspa_ready": False,
        "workshop_status": "provisioning",
        "workload_application_sync": "Synced",
        "showroom_application_sync": "Synced",
    }
    assert gate["observed_at_release"]["dspa_ready"] is True
    assert gate["observed_at_release"]["workshop_status"] == "ready"


def test_agentops_seat_proved_secret_boundary_and_participant_functionality():
    evidence = _evidence()
    checks = evidence["checks"]

    assert checks["runtime_secret_boundary"]["maas_api_key_present_in_argo_application"] is False
    assert checks["runtime_secret_boundary"]["maas_api_key_retained_after_reclaim"] is False
    assert checks["showroom_content"]["pages_http_200"] == 11
    assert checks["terminal_scope"]["create_deployments_in_assigned_namespace"] is True
    assert checks["terminal_scope"]["get_pods_in_openshift_logging"] is False
    assert checks["embedding_ingestion"] == {
        "status": "pass",
        "documents": 8,
        "chunks": 41,
        "embedded_chunks": 41,
        "dimensions_min": 768,
        "dimensions_max": 768,
    }
    assert checks["agent_websocket"]["terminal_event"] == "done"
    assert checks["mlflow_trace"]["span_count"] == 7
    assert checks["openshift_logging"]["own_namespace_marker_http_status"] == 200
    assert checks["openshift_logging"]["cross_namespace_query_http_status"] == 403


def test_agentops_seat_reclaimed_without_overclaiming_scale_or_public_access():
    evidence = _evidence()

    assert evidence["cleanup"] == {
        "status": "pass",
        "observed_within_seconds": 50,
        "remaining_namespaces": 0,
        "remaining_applications": 0,
        "remaining_persistent_volumes": 0,
        "remaining_temporary_log_test_resources": 0,
        "showroom_terminal_pv_deleted_automatically": True,
        "manual_permission_repair_required": False,
    }
    assert evidence["order"]["exposure_policy"] == "internal"
    assert "public-code" in evidence["certification_boundary"]
    assert "five" in evidence["certification_boundary"]
    assert evidence["security"]["secrets_included"] is False
    assert evidence["security"]["credential_values_logged"] is False
    assert len(evidence["remaining_release_gates"]) >= 8
