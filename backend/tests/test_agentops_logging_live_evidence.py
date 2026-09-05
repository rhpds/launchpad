"""Contract for the Arena one-seat OpenShift Logging evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-logging-live-2026-09-05.json"


def test_supported_logging_stack_is_live_for_the_one_seat_pilot():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/agentops-live-seat-evidence/v4"
    assert evidence["cluster_id"] == "arena"
    assert evidence["result"] == "partial"
    assert evidence["operators"] == {
        "loki_operator": {"version": "6.6.0", "phase": "Succeeded"},
        "cluster_logging": {"version": "6.6.0", "phase": "Succeeded"},
        "cluster_observability_operator": {
            "version": "1.5.2",
            "phase": "Succeeded",
        },
    }
    logging = evidence["shared_logging"]
    assert logging["lokistack"]["ready"] is True
    assert logging["cluster_log_forwarder"]["ready"] is True
    assert logging["cluster_log_forwarder"]["application_namespace_filter"] == (
        "launchpad-*"
    )
    assert logging["console_ui_plugin"] == {
        "name": "logging",
        "available": True,
        "degraded": False,
    }
    assert logging["pods"]["container_restarts"] == 0


def test_participant_can_read_only_its_assigned_namespace_logs():
    evidence = json.loads(EVIDENCE.read_text())
    authorization = evidence["participant_authorization"]

    assert authorization["edit_only_own_query_http_status"] == 403
    assert authorization["application_log_role"] == (
        "cluster-logging-application-view"
    )
    assert authorization["own_namespace_query_http_status"] == 200
    assert authorization["own_marker_count"] > 0
    assert authorization["own_result_streams"] > 0
    assert authorization["cross_namespace_query_http_status"] == 403
    assert evidence["security"]["cross_namespace_access_denied"] is True


def test_logging_evidence_preserves_scale_boundaries_and_secret_safety():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["shared_logging"]["lokistack"]["size"] == "1x.demo"
    assert "pilot MinIO" in evidence["shared_logging"]["storage"]["object_store"]
    assert len(evidence["scale_blockers"]) == 4
    assert evidence["cleanup"]["namespace_removed"] is True
    assert evidence["cleanup"]["observed_under_seconds"] <= 45
    assert evidence["security"]["secrets_included"] is False
    assert evidence["security"]["credential_values_logged"] is False
