"""Immutable contract for the second exact September agentic-trio rehearsal."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "evidence/september-17-agentic-trio-run02-red-2026-09-06.json"
)
CHECKSUM = EVIDENCE.with_suffix(".json.sha256")


def test_exact_trio_run02_records_failures_without_overclaiming():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema"] == "launchpad.redhat.com/event-certification/v1"
    assert evidence["overall_status"] == "RED"
    assert evidence["cluster_id"] == "arena"
    assert evidence["workshops"][0]["seats_ready"] == 25
    assert evidence["placement_proof"]["multi_agent_distribution_balanced"] is True
    assert evidence["control_plane_failure"]["failure"] == "OOMKilled"
    assert evidence["execution_worker_failure"]["node"] == "rhgnr1"
    assert evidence["cancellation_race"]["completed_workshop_received_late_sessions"] == 2
    assert evidence["reconciler_failure"]["database_connection_timed_out"] is True
    assert evidence["cleanup"]["remaining_namespaces"] == 0
    assert evidence["cleanup"]["remaining_argocd_applications"] == 0
    assert evidence["rubric"]["score"] < evidence["rubric"]["required"]
    assert evidence["release_decision"] == "not-certified"


def test_exact_trio_run02_evidence_is_hash_verified():
    expected = CHECKSUM.read_text().split()[0]
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
