"""The acceptance renderer must transcribe the scan exactly and never widen it."""

import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'scripts/check_backend_staging_security.py'
RENDER = ROOT / 'scripts/render_risk_acceptance.py'
REVISION = 'a' * 40
IMAGE = 'example.invalid/candidate:git-test'
IMAGE_ID = 'sha256:' + 'd' * 64
DIGEST = 'sha256:' + 'e' * 64

TODAY = dt.datetime.now(dt.timezone.utc).date()
SIGNED = (TODAY - dt.timedelta(days=1)).isoformat()
EXPIRES = (TODAY + dt.timedelta(days=90)).isoformat()


def _match(severity='High', identifier='CVE-example', package='example-package'):
    return {
        'vulnerability': {'id': identifier, 'severity': severity, 'fix': {'state': 'fixed'}},
        'artifact': {'name': package, 'type': 'rpm'},
    }


def _report(matches, *, ignored=(), digest=DIGEST):
    report = {
        'matches': list(matches),
        'descriptor': {'name': 'grype', 'configuration': {}},
        'source': {'type': 'image', 'target': {
            'userInput': IMAGE, 'imageID': IMAGE_ID,
        }},
    }
    if digest is not None:
        report['source']['target']['manifestDigest'] = digest
    if ignored:
        report['ignoredMatches'] = list(ignored)
    return report


def _module():
    spec = importlib.util.spec_from_file_location('render_risk_acceptance', RENDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build(report, **overrides):
    kwargs = {
        'component': 'terminal',
        'owner_role': 'launchpad-platform-security-reviewer',
        'owner_signature': 'reviewer 2026-11-24',
        'signed_on': SIGNED,
        'expires_on': EXPIRES,
        'source_revision': REVISION,
        'rationale': 'Reviewed scope.',
        'report_sha256': hashlib.sha256(b'{}').hexdigest(),
        'candidate_digest': None,
        'digest_pending': True,
    }
    kwargs.update(overrides)
    return _module().build_record(report, **kwargs)


def test_renderer_enumerates_only_blocking_findings_deduplicated_and_sorted():
    record = _build(_report([
        _match('High', 'CVE-b', 'z-package'),
        _match('Critical', 'CVE-a', 'm-package'),
        _match('Medium', 'CVE-c', 'a-package'),
        _match('High', 'CVE-b', 'z-package'),
    ]))
    assert [(entry['id'], entry['package'], entry['severity'])
            for entry in record['accepted']] == [
        ('CVE-a', 'm-package', 'Critical'),
        ('CVE-b', 'z-package', 'High'),
    ]


def test_renderer_refuses_to_cover_a_suppressed_finding():
    with pytest.raises(ValueError, match='suppress'):
        _build(_report([_match()], ignored=[_match('Critical', 'CVE-hidden')]))


def test_renderer_refuses_a_report_with_nothing_to_accept():
    with pytest.raises(ValueError, match='no High, Critical or Unrated'):
        _build(_report([_match('Medium')]))


def test_renderer_refuses_a_finding_it_cannot_name_exactly():
    match = _match()
    del match['artifact']['name']
    with pytest.raises(ValueError, match='package name'):
        _build(_report([match]))


@pytest.mark.parametrize('signed_on,expires_on,reason', [
    ((TODAY - dt.timedelta(days=30)).isoformat(),
     (TODAY - dt.timedelta(days=1)).isoformat(), 'expired'),
    ((TODAY + dt.timedelta(days=2)).isoformat(), EXPIRES, 'future'),
])
def test_renderer_refuses_a_record_the_gate_would_reject(tmp_path, signed_on, expires_on, reason):
    # build_record only transcribes; the gate's validator runs in main(), so the
    # refusal has to be observed through the CLI and no file may be left behind.
    scan = tmp_path / 'inventory.json'
    scan.write_text(json.dumps(_report([_match()])))
    acceptance = tmp_path / 'acceptance.json'
    process = subprocess.run(
        [sys.executable, str(RENDER), str(scan), '--component', 'terminal',
         '--owner-role', 'launchpad-platform-security-reviewer',
         '--owner-signature', 'reviewer 2026-11-24',
         '--signed-on', signed_on, '--expires-on', expires_on,
         '--source-revision', REVISION, '--rationale', 'Reviewed scope.',
         '--digest-pending', '--output', str(acceptance)],
        check=False, capture_output=True, text=True,
    )
    assert process.returncode == 2
    assert reason in process.stderr
    assert not acceptance.exists()


def test_rendered_record_and_scan_are_accepted_by_the_gate(tmp_path):
    report = _report([_match('High'), _match('Critical', 'CVE-other', 'other-package')])
    scan = tmp_path / 'inventory.json'
    scan.write_text(json.dumps(report))
    acceptance = tmp_path / 'acceptance.json'
    rendered = subprocess.run(
        [sys.executable, str(RENDER), str(scan), '--component', 'terminal',
         '--owner-role', 'launchpad-platform-security-reviewer',
         '--owner-signature', 'reviewer 2026-11-24',
         '--signed-on', SIGNED, '--expires-on', EXPIRES,
         '--source-revision', REVISION, '--rationale', 'Reviewed scope.',
         '--candidate-digest', DIGEST, '--output', str(acceptance)],
        check=False, capture_output=True, text=True,
    )
    assert rendered.returncode == 0, rendered.stderr
    decision = subprocess.run(
        [sys.executable, str(GATE), str(scan), '--component', 'terminal',
         '--expected-image', IMAGE, '--expected-image-id', IMAGE_ID,
         '--acceptance', str(acceptance), '--source-revision', REVISION],
        check=False, capture_output=True, text=True,
    )
    assert decision.returncode == 0, decision.stdout + decision.stderr
    result = json.loads(decision.stdout)
    assert result['risk_acceptance'] == 'GRANTED'
    assert result['accepted_high_matches'] == 1
    assert result['accepted_critical_matches'] == 1
    assert result['acceptance']['digest_binding'] == 'BOUND'
    assert result['acceptance']['report_sha256'] == hashlib.sha256(scan.read_bytes()).hexdigest()


def test_renderer_refuses_a_digest_that_does_not_match_the_report(tmp_path):
    scan = tmp_path / 'inventory.json'
    scan.write_text(json.dumps(_report([_match()])))
    process = subprocess.run(
        [sys.executable, str(RENDER), str(scan), '--component', 'terminal',
         '--owner-role', 'r', '--owner-signature', 's', '--signed-on', SIGNED,
         '--expires-on', EXPIRES, '--source-revision', REVISION,
         '--rationale', 'r', '--candidate-digest', 'sha256:' + 'f' * 64],
        check=False, capture_output=True, text=True,
    )
    assert process.returncode == 2
    assert 'does not match the digest' in process.stderr
