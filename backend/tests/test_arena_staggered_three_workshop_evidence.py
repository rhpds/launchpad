"""Contract for the Arena staggered 3x25 internal pilot evidence."""
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/arena-staggered-three-workshops-2026-09-04.json"


def test_staggered_three_workshop_evidence_proves_the_intended_boundary():
    evidence = json.loads(EVIDENCE.read_text())

    assert evidence["schema_version"] == "1.0"
    assert evidence["outcome"] == "pass"
    assert evidence["scope"] == "internal-staggered-three-workshop-pilot"
    assert evidence["cluster"] == "arena"
    assert evidence["public_access_certified"] is False
    assert evidence["simultaneous_provisioning_certified"] is False

    workshops = evidence["workshops"]
    assert [workshop["catalog_item_id"] for workshop in workshops] == [
        "intel-llm-cpu-serving",
        "intel-xeon6-agent-201",
        "intel-llm-tool-calling",
    ]
    assert all(workshop["seat_count"] == 25 for workshop in workshops)
    assert all(workshop["all_seats_ready"] is True for workshop in workshops)
    assert sum(workshop["seat_count"] for workshop in workshops) == 75
    for previous, current in zip(workshops, workshops[1:]):
        assert datetime.fromisoformat(current["requested_at"].replace("Z", "+00:00")) >= datetime.fromisoformat(
            previous["ready_at"].replace("Z", "+00:00")
        )

    participants = evidence["concurrent_participant_use"]
    assert participants["participants_started"] == 75
    assert participants["participants_successful"] == 75
    assert participants["batch_seconds"] <= 120
    assert participants["cpu_serving"]["successful"] == 25
    assert participants["cpu_serving"]["p95_seconds"] < 60
    assert participants["agent_201"]["successful"] == 25
    assert participants["agent_201"]["p95_seconds"] < 120
    assert participants["tool_calling"]["successful"] == 25
    assert participants["tool_calling"]["p95_seconds"] < 15

    isolation = evidence["participant_isolation"]
    assert isolation["default_project_matches_seat"] == 75
    assert isolation["own_namespace_edit_allowed"] == 75
    assert isolation["cross_seat_read_denied"] == 75

    cleanup = evidence["sequential_cleanup"]
    assert cleanup["workshop_order"] == [
        "intel-llm-cpu-serving",
        "intel-xeon6-agent-201",
        "intel-llm-tool-calling",
    ]
    assert cleanup["completed_workshops"] == 3
    assert cleanup["remaining_scoped_namespaces"] == 0
    assert cleanup["remaining_scoped_routes"] == 0
    assert cleanup["remaining_scoped_applications"] == 0
    assert cleanup["remaining_scoped_rolebindings"] == 0

    assert all(
        row["status"] == "GREEN-live"
        for row in evidence["red_green_matrix"]
        if row["critical"]
    )
    assert evidence["gate_rubric"]["score"] == 100
    assert evidence["gate_rubric"]["required"] == 100
