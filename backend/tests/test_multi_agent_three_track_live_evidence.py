from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/multi-agent-three-track-showroom-live-2026-09-06.json"
CHECKSUM = ROOT / "evidence/multi-agent-three-track-showroom-live-2026-09-06.json.sha256"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_three_tracks_are_present_in_one_lab_environment():
    evidence = _evidence()

    assert evidence["result"] == "pass-one-lab-three-track-showroom"
    assert evidence["cluster_ref"] == "arena"
    assert evidence["order"]["seat_count"] == 1
    assert evidence["order"]["environment_count"] == 1
    assert evidence["checks"]["one_lab_contract"] == {
        "status": "pass",
        "single_environment": True,
        "track_count": 3,
        "chooser_http_status": 200,
        "chooser_marker_present": True,
    }
    assert [track["id"] for track in evidence["tracks"]] == [
        "track-1-local",
        "track-2-openshift",
        "track-3-blueprint",
    ]
    assert all(track["showroom_http_status"] == 200 for track in evidence["tracks"])
    assert all(track["content_marker_present"] for track in evidence["tracks"])


def test_track_two_runtime_is_green_without_overclaiming_track_three():
    evidence = _evidence()
    statuses = {track["id"]: track for track in evidence["tracks"]}

    assert statuses["track-2-openshift"]["certification_status"] == "GREEN-live-runtime"
    assert statuses["track-3-blueprint"]["optional_runtime_integrations_certified"] is False
    assert evidence["checks"]["track_2_runtime"]["agents_discovered"] == 3
    assert evidence["checks"]["track_2_runtime"]["multi_agent_steps"] == 3
    assert evidence["checks"]["track_2_runtime"]["workflow_errors"] == 0
    assert evidence["validation_matrix"]["track_3_optional_runtime"] == "RED-not-certified"
    assert evidence["release_boundary"]["general_availability"] is False


def test_three_track_run_reclaimed_with_zero_residue():
    cleanup = _evidence()["cleanup"]

    assert cleanup["status"] == "pass"
    assert cleanup["model_key_cleared"] is True
    for resource in (
        "remaining_namespaces",
        "remaining_applications",
        "remaining_role_bindings",
        "remaining_persistent_volume_claims",
        "remaining_persistent_volumes",
        "remaining_routes",
        "remaining_secrets",
    ):
        assert cleanup[resource] == 0


def test_three_track_live_evidence_checksum_matches_artifact():
    expected, filename = CHECKSUM.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
