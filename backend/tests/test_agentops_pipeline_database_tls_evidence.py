"""Contract for the Arena AgentOps pipeline database TLS live evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-pipeline-database-tls-live-2026-09-05.json"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_pipeline_database_evidence_proves_verified_tls_and_ready_workload():
    evidence = _evidence()
    live = evidence["green"]["live"]

    assert evidence["cluster"]["cluster_id"] == "arena"
    assert evidence["result"] == (
        "pass-internal-one-seat-with-rhoai-compatibility-workaround"
    )
    assert live["workload_application"] == "Synced/Healthy"
    assert live["dspa_ready"] is True
    assert live["plaintext_database_connection_denied"] is True
    assert live["verified_database_tls"] is True
    assert live["database_tls_version"] == "TLSv1.3"
    assert live["database_require_secure_transport"] is True
    assert live["pipeline_schema_tables"] > 0
    assert live["not_fully_ready_pods"] == 0
    assert live["container_restarts"] == 0


def test_pipeline_database_evidence_proves_cleanup_and_preserves_boundaries():
    evidence = _evidence()
    cleanup = evidence["cleanup"]
    limitations = " ".join(evidence["limitations"])

    assert cleanup["launchpad_session_status"] == "reclaimed"
    assert cleanup["model_key_retained"] is False
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_applications"] == 0
    assert cleanup["remaining_persistent_volumes"] == 0
    assert cleanup["manual_resource_deletion_required"] is False
    assert "podToPodTLS remains disabled" in limitations
    assert "does not promote AgentOps beyond its one-seat catalog cap" in limitations


def test_pipeline_database_evidence_tracks_every_observed_red_regression():
    evidence = _evidence()

    assert len(evidence["red"]["local"]) >= 2
    assert len(evidence["red"]["live"]) == 2
    assert evidence["green"]["integration"]["argo_ignore_difference"] == {
        "resource": "ConfigMap/agentops-pipeline-service-ca",
        "json_pointer": "/data",
        "sync_option": "RespectIgnoreDifferences=true",
    }
