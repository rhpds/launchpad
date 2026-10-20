"""A fixable-only release scan must not silently grant staging qualification."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _gate():
    spec = importlib.util.spec_from_file_location(
        "staging_security", ROOT / "scripts/check_backend_staging_security.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _match(severity="High", fix="not-fixed", identifier="CVE-example"):
    return {
        "vulnerability": {"id": identifier, "severity": severity, "fix": {"state": fix}},
        "artifact": {"name": "example-package", "type": "rpm"},
    }


@pytest.mark.parametrize("state", ["not-fixed", "wont-fix", "fixed", ""])
def test_high_findings_block_staging_regardless_of_fix_state(state):
    result = _gate().summarize({"matches": [_match(fix=state)]})
    assert result["staging_security_gate"] == "BLOCKED"
    assert result["high_matches"] == 1
    assert result["risk_acceptance"] == "NOT-GRANTED"


def test_critical_blocks_and_duplicates_are_not_distinct_vulnerabilities():
    result = _gate().summarize({"matches": [_match("Critical"), _match("Critical")]})
    assert result["critical_matches"] == 2
    assert result["distinct_high_critical_ids"] == 1
    assert result["staging_security_gate"] == "BLOCKED"


def test_clean_scan_only_passes_security_scan_not_platform_staging():
    result = _gate().summarize({"matches": [_match("Medium")]})
    assert result["staging_security_gate"] == "PASS-SCAN-ONLY"
    assert result["platform_staging_qualified"] is False


@pytest.mark.parametrize("report", [{}, {"matches": None}, {"matches": [{}]}])
def test_malformed_inventory_fails_closed(report):
    with pytest.raises(ValueError):
        _gate().summarize(report)


def test_suppressed_high_cannot_disappear_from_staging_decision():
    result = _gate().summarize({"matches": [], "ignoredMatches": [_match()]})
    assert result["staging_security_gate"] == "BLOCKED"
    assert result["suppressed_high_matches"] == 1


def test_fixable_only_report_cannot_be_used_for_staging():
    report = {"matches": [], "descriptor": {"configuration": {"only-fixed": True}}}
    with pytest.raises(ValueError, match="filtered"):
        _gate().summarize(report)


@pytest.mark.parametrize('severity', ['High', 'Critical', 'Unknown'])
@pytest.mark.parametrize('suppressed', [False, True])
def test_terminal_full_inventory_blocks_without_risk_acceptance(severity, suppressed):
    report = {'matches': [] if suppressed else [_match(severity)]}
    if suppressed:
        report['ignoredMatches'] = [_match(severity)]
    result = _gate().summarize(report, component='terminal')
    assert result['schema'] == 'launchpad/terminal-staging-security/v1'
    assert result['staging_security_gate'] == 'BLOCKED'
    assert result['risk_acceptance'] == 'NOT-GRANTED'
    assert result['platform_staging_qualified'] is False


def test_unknown_component_is_not_accepted():
    with pytest.raises(ValueError, match='component'):
        _gate().summarize({'matches': []}, component='unreviewed')


@pytest.mark.parametrize('severity,exit_code', [('Unknown', 1), ('High', 1), ('Medium', 0)])
def test_terminal_cli_returns_gate_status_and_binds_report_hash(tmp_path, severity, exit_code):
    import hashlib

    report = tmp_path / 'inventory.json'
    raw = json.dumps({'matches': [_match(severity)]}).encode()
    report.write_bytes(raw)
    process = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/check_backend_staging_security.py'),
         str(report), '--component', 'terminal'], check=False, capture_output=True, text=True,
    )
    assert process.returncode == exit_code
    decision = json.loads(process.stdout)
    assert decision['schema'] == 'launchpad/terminal-staging-security/v1'
    assert decision['report_sha256'] == hashlib.sha256(raw).hexdigest()
    assert decision['platform_staging_qualified'] is False
