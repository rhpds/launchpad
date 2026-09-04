"""Contract for the Arena five-seat Agent 201 certification evidence."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/intel-agent-201-five-seat-2026-09-04.json"


def test_agent_201_five_seat_evidence_is_complete_and_scoped():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema_version"] == "1.0"
    assert evidence["outcome"] == "pass"
    assert evidence["scope"] == "internal-five-seat-workshop"
    assert evidence["cluster"] == "arena"
    assert evidence["catalog_item_id"] == "intel-xeon6-agent-201"
    assert evidence["model"] == "granite-3.2-8b-tools"
    assert evidence["seat_count"] == 5
    assert evidence["public_access_certified"] is False
    assert evidence["twenty_five_seat_certified"] is False

    provisioning = evidence["provisioning"]
    assert provisioning["all_seats_ready"] is True
    assert provisioning["collective_ready_seconds"] <= 120
    assert provisioning["unique_session_count"] == 5
    assert provisioning["unique_namespace_count"] == 5
    assert provisioning["session_labels_match"] == 5
    assert provisioning["healthy_synced_argocd_applications"] == 5

    participant = evidence["participant_validation"]
    assert participant["showroom_http_200"] == 5
    assert participant["guide_http_200"] == 5
    assert participant["model_connection_values_rendered"] == 5
    assert participant["default_project_matches_seat"] == 5
    assert participant["own_namespace_edit_allowed"] == 5
    assert participant["cross_seat_read_denied"] == 5
    assert participant["participant_deployments_ready"] == 15
    assert participant["participant_pods_zero_restarts"] == 15

    agent = evidence["concurrent_agent_journeys"]
    assert agent["successful_journeys"] == 5
    assert agent["fallback_free_journeys"] == 5
    assert agent["structured_briefs"] == 5
    assert agent["all_three_mcp_tools_used"] == 5
    assert agent["p95_seconds"] < 240

    cleanup = evidence["cleanup"]
    assert cleanup["all_seats_reclaimed"] is True
    assert cleanup["completed_seconds"] <= 600
    assert cleanup["remaining_namespaces"] == 0
    assert cleanup["remaining_routes"] == 0
    assert cleanup["remaining_applications"] == 0
    assert cleanup["remaining_rolebindings"] == 0

    assert all(
        row["status"] == "GREEN-live"
        for row in evidence["red_green_matrix"]
        if row["critical"]
    )
    assert evidence["gate_rubric"]["score"] == 100
    assert evidence["gate_rubric"]["required"] == 100


def test_agent_201_certification_drivers_enforce_the_participant_boundary():
    seat_script = (ROOT / "scripts/certify-agent-201-seat.sh").read_text()
    journey_script = (ROOT / "scripts/certify-agent-201-journey.sh").read_text()

    assert "*config-arena*" in seat_script
    assert "refusing to mutate a non-Arena cluster" in seat_script
    assert "deploy/showroom -c terminal" in seat_script
    assert "litellm-api-key" in seat_script
    assert "ADVISOR_MODEL" in seat_script
    assert "*config-arena*" in journey_script
    assert "refusing to validate a non-Arena cluster" in journey_script
    assert 'select(.error != null)' in journey_script
    assert "intel_hardware_lookup" in journey_script
    assert "openshift_capabilities" in journey_script
    assert "reference_architectures" in journey_script
