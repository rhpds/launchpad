"""Contract for the September 17 Arena workshop release gate."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READINESS = ROOT / "evidence/september-17-three-workshop-readiness-2026-09-05.json"
RUNBOOK = ROOT / "docs/september-17-three-workshop-readiness.md"


def test_event_readiness_manifest_keeps_the_exact_workshop_target_and_budget():
    readiness = json.loads(READINESS.read_text())

    assert readiness["schema"] == "launchpad.redhat.com/event-readiness/v1"
    assert readiness["event_date"] == "2026-09-17"
    assert readiness["cluster_id"] == "arena"
    assert readiness["provisioning_mode"] == "staggered"
    assert readiness["concurrent_participant_seats"] == 75

    workshops = readiness["workshops"]
    assert [workshop["catalog_item_id"] for workshop in workshops] == [
        "agentops-observability",
        "intel-llm-cpu-serving",
        "intel-xeon6-agent-201",
    ]
    assert all(workshop["seat_count"] == 25 for workshop in workshops)
    assert workshops[0]["release_status"] == "RED"
    assert all(workshop["release_status"] == "GREEN-live-25" for workshop in workshops[1:])

    declared = readiness["declared_event_reservation"]
    assert declared == {
        "cpu_millicores": 89500,
        "memory_mib": 239200,
        "pod_slots": 525,
        "storage_gib_minimum": 750,
    }
    protected = readiness["admission_target_with_twenty_percent_headroom"]
    assert protected == {
        "cpu_millicores": 107400,
        "memory_mib": 287040,
        "pod_slots": 630,
        "storage_gib_minimum": 900,
    }

    assert readiness["previous_pattern_evidence"] == (
        "evidence/arena-staggered-three-workshops-2026-09-04.json"
    )
    assert readiness["public_access_certified"] is False
    assert readiness["overall_status"] == "RED"
    assert readiness["next_gate"] == "agentops-one-seat-launchpad"


def test_event_runbook_names_every_gate_and_does_not_overclaim_capacity():
    runbook = RUNBOOK.read_text()

    for value in (
        "September 17, 2026",
        "agentops-observability",
        "intel-llm-cpu-serving",
        "intel-xeon6-agent-201",
        "1 -> 5 -> 25",
        "89,500m",
        "239,200 MiB",
        "525",
        "750 GiB",
        "evidence/arena-staggered-three-workshops-2026-09-04.json",
    ):
        assert value in runbook

    normalized_runbook = " ".join(runbook.lower().split())
    assert "public access is not certified" in normalized_runbook
    assert "current free arena capacity must be measured live" in normalized_runbook
    assert "AgentOps first" in runbook
    assert "zero residue" in runbook
