from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_advanced_virtualization_probes_require_non_overlapping_restart_and_ledger_continuity():
    probe = (REPO_ROOT / "scripts/certify-virtualization-ai-seat.sh").read_text()
    assert 'restart_and_verify_ledger "$service" "$endpoint/op-401-cert"' in probe
    assert 'restart_and_verify_ledger "$service" "$endpoint/qualification-cert-001"' in probe
    assert '[[ "$strategy" == Recreate ]] || exit 1' in probe
    assert '[[ "$ledger_after" == "$ledger_before" ]] || exit 1' in probe
    assert "restart_evidence_preserved:$restart_evidence_preserved" in probe


def test_virtualization_probe_emits_only_the_result_json_on_stdout() -> None:
    probe = (
        REPO_ROOT / "scripts" / "certify-virtualization-ai-seat.sh"
    ).read_text()

    wait_lines = [line.strip() for line in probe.splitlines() if " wait " in line]

    assert wait_lines
    assert all(
        line.endswith(">/dev/null") or line.endswith(">/dev/null 2>&1 || true")
        for line in wait_lines
    )
