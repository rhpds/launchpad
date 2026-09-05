"""Contract for the Arena shared MLflow and integrated AgentOps component run."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-mlflow-live-2026-09-05.json"


def test_shared_mlflow_is_functional_and_workspace_isolated():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/agentops-live-seat-evidence/v3"
    assert evidence["cluster_id"] == "arena"
    assert evidence["result"] == "partial"
    assert evidence["deployment"]["launchpad_order_created"] is False

    mlflow = evidence["checks"]["shared_mlflow"]
    assert mlflow["status"] == "pass"
    assert mlflow["version"] == "3.14.0"
    assert mlflow["available"] is True
    assert mlflow["assigned_workspace_write_http_status"] == 200
    assert mlflow["cross_workspace_write_http_status"] == 403
    assert mlflow["cross_workspace_names_leaked"] == 0

    trace = evidence["checks"]["mlflow_trace"]
    assert trace["status"] == "pass"
    assert trace["trace_count"] == 1
    assert trace["state"] == "OK"
    assert trace["span_count"] == 7


def test_integrated_agentops_component_and_automatic_cleanup_are_green():
    evidence = json.loads(EVIDENCE.read_text())

    workload = evidence["workload"]
    assert workload["running_pods"] == 13
    assert workload["completed_jobs"] == 1
    assert workload["container_restarts"] == 0
    assert workload["requested_cpu_millicores"] == 2080
    assert workload["requested_memory_mib"] == 5720
    assert workload["pvc_count"] == 3
    assert workload["reservation_with_showroom"] == {
        "cpu_millicores": 2500,
        "memory_mib": 7168,
        "pods": 15,
        "storage_gib": 30,
    }

    assert evidence["checks"]["embedding_ingestion"]["embedded_chunks"] == 41
    assert evidence["checks"]["data_science_pipelines"]["ready"] is True
    assert evidence["checks"]["agent_websocket"]["terminal_event"] == "done"

    cleanup = evidence["cleanup"]
    assert cleanup["automatic"] is True
    assert cleanup["namespace_delete_seconds"] == 59
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_pvs"] == 0
    assert cleanup["remaining_nfs_directories"] == 0
    assert cleanup["manual_repair_required"] is False


def test_live_evidence_keeps_uncertified_release_gates_red():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["checks"]["trusted_external_tls"]["status"] == "fail"
    assert evidence["checks"]["pipeline_database_tls"]["status"] == "fail"
    assert evidence["checks"]["launchpad_showroom_entitlement"]["status"] == "not-run"
    assert evidence["checks"]["openshift_logging"]["status"] == "not-run"
    assert evidence["security"]["secrets_included"] is False
