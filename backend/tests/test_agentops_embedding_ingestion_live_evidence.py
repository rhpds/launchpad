"""Contract for the second live AgentOps seat and Arena capacity evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-embedding-ingestion-live-2026-09-05.json"


def test_live_agentops_seat_proves_complete_embedding_ingestion_and_search():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/agentops-live-seat-evidence/v2"
    assert evidence["cluster_id"] == "arena"
    assert evidence["result"] == "partial"
    assert evidence["deployment"]["launchpad_order_created"] is False

    workload = evidence["workload"]
    assert workload["steady_ready_pods"] == 12
    assert workload["completed_jobs"] == 1
    assert workload["container_restarts"] == 0
    assert workload["requested_cpu_millicores"] == 1730
    assert workload["requested_memory_mib"] == 4964

    embedding = evidence["checks"]["embedding_ingestion"]
    assert embedding == {
        "status": "pass",
        "documents": 8,
        "chunks": 41,
        "embedded_chunks": 41,
        "missing_embeddings": 0,
        "dimensions_min": 768,
        "dimensions_max": 768,
    }
    retrieval = evidence["checks"]["semantic_retrieval"]
    assert retrieval["status"] == "pass"
    assert [result["section_ref"] for result in retrieval["top_results"]] == [
        "Minimum Credit Score",
        "Mortgage Insurance Premium",
        "DTI Limits",
    ]
    assert evidence["checks"]["agent_websocket"]["terminal_event"] == "done"
    assert evidence["checks"]["mlflow_tracking"]["status"] == "fail"


def test_live_capacity_and_cleanup_evidence_preserves_the_hard_pod_slot_blocker():
    evidence = json.loads(EVIDENCE.read_text())
    capacity = evidence["arena_capacity"]

    assert capacity["schedulable_workers"] == 2
    assert capacity["schedulable_pod_slots"] == 500
    assert capacity["running_pods_on_workers"] == 193
    assert capacity["event_declared_pods"] == 500
    assert capacity["projected_pods_without_headroom"] == 693
    assert capacity["projected_pods_with_event_headroom"] == 793
    assert capacity["event_fits_current_workers"] is False
    assert capacity["recommended_additional_250_pod_workers"] == 2

    cleanup = evidence["cleanup"]
    assert cleanup["namespace_deleted"] is True
    assert cleanup["remaining_pvs"] == 0
    assert cleanup["remaining_nfs_directories"] == 0
    assert cleanup["remaining_labeled_objects"] == 0
    assert cleanup["storage_defect_discovered"] == "nfs-storage uses Retain"
    assert cleanup["corrective_storage_class"] == "launchpad-nfs-ephemeral"
    assert cleanup["corrective_storage_class_live_probe"] == "pass"
