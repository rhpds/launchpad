from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/agentops-one-seat-live-2026-09-04.json"


def test_agentops_one_seat_live_evidence_is_honest_and_reclaimable():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/agentops-live-seat-evidence/v1"
    assert evidence["cluster_id"] == "arena"
    assert evidence["repository_revision"] == "6936ee6b9d64df8ccda8902279b8cc3a1e4c0545"
    assert evidence["result"] == "blocked"
    assert evidence["security"]["secrets_included"] is False

    checks = evidence["checks"]
    assert checks["api_and_database_health"]["status"] == "pass"
    assert checks["generation_endpoint"]["status"] == "pass"
    assert checks["agent_websocket"]["status"] == "pass"
    assert checks["dspa"]["status"] == "pass"
    assert checks["mortgage_ui_route"]["status"] == "pass"
    assert checks["grafana_route"]["status"] == "pass"
    assert checks["trusted_route_tls"]["status"] == "fail"
    assert checks["embedding_endpoint"]["status"] == "fail"
    assert checks["mlflow_server"]["status"] == "fail"

    footprint = evidence["measured_footprint"]
    assert footprint["chart"] == {
        "cpu_millicores": 1730,
        "memory_mib": 4964,
        "pods": 13,
        "storage_gib": 30,
    }
    assert footprint["reservation_with_showroom"] == {
        "cpu_millicores": 2000,
        "memory_mib": 6144,
        "pods": 14,
        "storage_gib": 30,
    }

    assert evidence["reclaim"]["status"] == "pass"
    assert evidence["reclaim"]["remaining_namespaces"] == 0
    assert evidence["reclaim"]["remaining_namespaced_resources"] == 0


def test_agentops_live_evidence_keeps_failed_requirements_out_of_green_live():
    evidence = json.loads(EVIDENCE.read_text())
    matrix = {row["id"]: row for row in evidence["red_green_matrix"]}

    assert matrix["LIVE-AGENTOPS-007"]["status"] == "blocked"
    assert matrix["LIVE-AGENTOPS-013"]["status"] == "GREEN-live"
    assert matrix["LIVE-AGENTOPS-014"]["status"] == "RED-live"
    assert matrix["LIVE-AGENTOPS-015"]["status"] == "RED-live"
