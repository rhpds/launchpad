from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/multi-agent-one-seat-live-2026-09-05.json"
CHECKSUM = ROOT / "evidence/multi-agent-one-seat-live-2026-09-05.json.sha256"


def _evidence() -> dict:
    return json.loads(EVIDENCE.read_text())


def test_multi_agent_internal_seat_proved_real_function_and_isolation():
    evidence = _evidence()

    assert evidence["schema"] == "launchpad.redhat.com/multi-agent-live-seat-evidence/v1"
    assert evidence["result"] == "pass-internal-one-seat-after-regression-retry"
    assert evidence["cluster_ref"] == "arena"
    assert evidence["order"]["seat_count"] == 1
    assert evidence["order"]["cluster_ref_persisted"] is True
    assert evidence["checks"]["readiness"]["agents_discovered"] == 3
    assert evidence["checks"]["multi_agent_journey"]["agents"] == [
        "research",
        "analyst",
        "executor",
    ]
    assert evidence["checks"]["multi_agent_journey"]["steps"] == 3
    assert evidence["checks"]["multi_agent_journey"]["mcp_steps"] == 3
    assert evidence["checks"]["multi_agent_journey"]["errors"] == 0
    assert evidence["checks"]["semantic_routing"]["status"] == "ok"
    assert evidence["checks"]["guardrails"]["blocked_steps"] == 3
    assert evidence["checks"]["terminal_scope"]["cross_namespace_read_denied"] is True
    assert evidence["checks"]["terminal_scope"]["node_list_denied"] is True


def test_multi_agent_internal_seat_proved_secret_boundary_and_zero_residue():
    evidence = _evidence()

    assert evidence["checks"]["runtime_secret_boundary"]["keys"] == [
        "AGENT_AUTH_TOKEN",
        "MODEL_API_KEY",
        "MODEL_ENDPOINT",
        "MODEL_NAME",
    ]
    assert evidence["checks"]["runtime_secret_boundary"]["secret_in_gitops"] is False
    assert evidence["cleanup"] == {
        "status": "pass",
        "seconds": 69,
        "remaining_namespaces": 0,
        "remaining_applications": 0,
        "remaining_persistent_volumes": 0,
        "remaining_image_pull_bindings": 0,
        "session_status": "reclaimed",
        "model_key_cleared": True,
    }
    assert evidence["security"]["contains_plaintext_credentials"] is False
    assert evidence["security"]["credential_values_logged"] is False


def test_multi_agent_evidence_does_not_overclaim_scale_public_or_clean_first_pass():
    evidence = _evidence()

    assert evidence["release_boundary"] == {
        "internal_one_seat_functional_gate": True,
        "clean_first_pass": False,
        "internal_five_seat_gate": False,
        "internal_twenty_five_seat_gate": False,
        "public_access_certified": False,
        "general_availability": False,
    }
    assert len(evidence["remaining_release_gates"]) >= 6


def test_multi_agent_live_evidence_checksum_matches_artifact():
    expected, filename = CHECKSUM.read_text().strip().split("  ", maxsplit=1)

    assert filename == EVIDENCE.name
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected
