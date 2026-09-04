"""Contract for the Arena five-seat Tool Calling certification evidence."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/intel-tool-calling-five-seat-2026-09-04.json"


def test_five_seat_evidence_is_complete_and_does_not_overclaim_scope():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema_version"] == "1.0"
    assert evidence["outcome"] == "pass"
    assert evidence["scope"] == "internal-five-seat-workshop"
    assert evidence["cluster"] == "arena"
    assert evidence["catalog_item_id"] == "intel-llm-tool-calling"
    assert evidence["seat_count"] == 5
    assert evidence["public_access_certified"] is False
    assert evidence["twenty_five_seat_certified"] is False

    assert evidence["provisioning"]["all_seats_ready"] is True
    assert evidence["provisioning"]["collective_ready_seconds"] <= 120
    assert evidence["provisioning"]["unique_session_count"] == 5
    assert evidence["provisioning"]["unique_namespace_count"] == 5

    assert evidence["participant_validation"]["showroom_http_200"] == 5
    assert evidence["participant_validation"]["guide_http_200"] == 5
    assert evidence["participant_validation"]["resolved_model_urls"] == 5
    assert evidence["participant_validation"]["default_project_matches_seat"] == 5
    assert evidence["participant_validation"]["own_namespace_edit_allowed"] == 5
    assert evidence["participant_validation"]["cross_seat_read_denied"] == 5
    assert evidence["participant_validation"]["complete_tool_protocol"] == "pass"

    assert evidence["concurrent_inference"]["successful_calls"] == 5
    assert evidence["concurrent_inference"]["structured_tool_calls"] == 5
    assert evidence["concurrent_inference"]["p95_seconds"] < 5

    cleanup = evidence["cleanup"]
    assert cleanup["all_seats_reclaimed"] is True
    assert cleanup["completed_seconds"] <= 600
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_routes"] == 0
    assert cleanup["remaining_applications"] == 0
    assert cleanup["remaining_cross_namespace_rolebindings"] == 0

    assert all(
        row["status"] == "GREEN-live"
        for row in evidence["red_green_matrix"]
        if row["critical"]
    )
