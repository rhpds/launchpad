"""Contract for the Arena shared MLflow PostgreSQL live evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-mlflow-postgres-live-2026-09-05.json"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_live_mlflow_postgres_evidence_is_tls_backed_and_current_generation():
    evidence = _evidence()
    live = evidence["green"]["live"]

    assert evidence["cluster"]["cluster_id"] == "arena"
    assert evidence["result"] == "pass-internal-shared-service"
    assert live["mlflow_available"] is True
    assert live["mlflow_generation"] == live["mlflow_operator_observed_generation"]
    assert live["postgres_tls"] is True
    assert live["postgres_tls_version"] == "TLSv1.3"
    assert live["mlflow_public_tables"] > 0
    assert live["observed_encrypted_mlflow_connections"] > 0


def test_live_mlflow_postgres_evidence_preserves_secret_and_scale_boundaries():
    evidence = _evidence()
    security = evidence["security"]
    limitations = " ".join(evidence["limitations"])

    assert security["backend_uri_source"] == "Secret/mlflow-postgres"
    assert security["backend_uri_present_in_git"] is False
    assert security["client_verification"] == (
        "verify-full through MLflow caBundleConfigMap"
    )
    assert "ReadWriteOnce" in limitations
    assert "does not promote AgentOps beyond its one-seat cap" in limitations
