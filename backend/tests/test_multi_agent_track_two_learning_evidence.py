"""RED/GREEN evidence contracts for the hands-on Track 2 learner path."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "evidence/runs"


def _load(name: str) -> dict:
    return json.loads((RUNS / name).read_text())


def _assert_checksum(name: str) -> None:
    evidence = RUNS / name
    expected, filename = (RUNS / f"{name}.sha256").read_text().strip().split("  ", 1)

    assert filename == evidence.name
    assert hashlib.sha256(evidence.read_bytes()).hexdigest() == expected


def test_participant_ui_authentication_reaches_green_live():
    name = "multi-agent-quickstart-1-seat-track2-learning-20260906-01.json"
    evidence = _load(name)
    result = evidence["seat_results"][0]["probe"]["result"]

    assert evidence["result"] == "GREEN-live"
    assert evidence["rubric"]["score"] == 100
    assert result["participant_ui_journey"] == {
        "executor_present": True,
        "http_error": False,
        "step_count_one": True,
    }
    assert all(count == 0 for count in evidence["cleanup"]["resource_counts"].values())
    _assert_checksum(name)


def test_direct_deployment_patch_is_retained_as_red_gitops_evidence():
    name = "multi-agent-quickstart-1-seat-track2-learning-20260906-02.json"
    evidence = _load(name)
    probe = evidence["seat_results"][0]["probe"]

    assert evidence["result"] == "RED-live"
    assert probe["passed"] is False
    assert probe["failure_stage"] == "learner-policy-apply"
    assert evidence["cleanup"]["status"] == "completed"
    assert all(count == 0 for count in evidence["cleanup"]["resource_counts"].values())
    _assert_checksum(name)
