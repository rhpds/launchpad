"""Contract for the live Multi-Agent 25-seat catalog promotion receipt."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/multi-agent-quickstart-25-seat-promotion-2026-09-06.json"


def test_multi_agent_internal_twenty_five_seat_promotion_is_live_and_auditable():
    receipt = json.loads(EVIDENCE.read_text())

    assert receipt["schema"] == "launchpad.redhat.com/catalog-promotion-evidence/v1"
    assert receipt["result"] == "GREEN-live-internal"
    assert receipt["cluster_id"] == "arena"
    assert receipt["catalog"] == {
        "catalog_item_id": "multi-agent-quickstart",
        "version": "0.2.3",
        "status": "draft",
        "certification_stage": "twenty-five-seat-certified",
        "max_workshop_seats": 25,
    }
    assert receipt["capacity_preview"]["http_status"] == 200
    assert receipt["capacity_preview"]["can_provision"] is True
    assert receipt["capacity_preview"]["selected_cluster"] == "arena"
    assert receipt["capacity_preview"]["seats_requested"] == 25
    assert receipt["capacity_preview"]["certification_override"] is False
    assert receipt["quality_gates"]["non_local_tests"] == {
        "passed": 1113,
        "deselected": 13,
        "failed": 0,
    }
    assert receipt["promotion_sequence"]["consecutive_green_live_runs"] == 3
    assert all(receipt["residue_audit"].values()) is False
    assert receipt["public_access_certified"] is False
    assert receipt["production_activation"] == "blocked"
