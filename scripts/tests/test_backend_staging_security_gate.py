"""A fixable-only release scan must not silently grant staging qualification."""

import datetime as dt
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


def _image_report():
    return {
        'matches': [],
        'source': {'type': 'image', 'target': {
            'userInput': 'example.invalid/candidate:git-test',
            'imageID': 'sha256:' + 'a' * 64,
            'manifestDigest': 'sha256:' + 'b' * 64,
        }},
        'descriptor': {'name': 'grype', 'configuration': {}},
    }


def test_image_gate_binds_report_to_candidate_and_retains_identity():
    result = _gate().summarize(
        _image_report(), expected_image='example.invalid/candidate:git-test',
        expected_image_id='sha256:' + 'a' * 64,
    )
    assert result['candidate_identity_verified'] is True
    assert result['image_id'] == 'sha256:' + 'a' * 64
    assert result['manifest_digest'] == 'sha256:' + 'b' * 64


@pytest.mark.parametrize('change', ['wrong-tag', 'wrong-id', 'not-image', 'missing-source',
                                  'missing-descriptor', 'wrong-scanner', 'missing-digest'])
def test_image_gate_rejects_stale_or_incomplete_candidate_report(change):
    report = _image_report()
    if change == 'wrong-tag':
        report['source']['target']['userInput'] = 'example.invalid/other:old'
    elif change == 'wrong-id':
        report['source']['target']['imageID'] = 'sha256:' + 'c' * 64
    elif change == 'not-image':
        report['source']['type'] = 'directory'
    elif change == 'missing-source':
        del report['source']
    elif change == 'missing-descriptor':
        del report['descriptor']
    elif change == 'wrong-scanner':
        report['descriptor']['name'] = 'unknown'
    else:
        del report['source']['target']['manifestDigest']
    with pytest.raises(ValueError):
        _gate().summarize(report, expected_image='example.invalid/candidate:git-test',
                          expected_image_id='sha256:' + 'a' * 64)


@pytest.mark.parametrize('setting,value', [('exclude', ['**/oc']), ('ignore-wontfix', True),
                                        ('only-notfixed', True), ('only-fixed', True)])
def test_filtered_candidate_inventory_cannot_qualify(setting, value):
    report = _image_report()
    report['descriptor']['configuration'][setting] = value
    with pytest.raises(ValueError, match='filtered'):
        _gate().summarize(report)


TODAY = dt.date(2026, 12, 1)
REVISION = 'a' * 40


def _acceptance(**overrides):
    record = {
        'schema': 'launchpad/risk-acceptance/v1',
        'component': 'terminal',
        'status': 'ACCEPTED-WITH-SCOPE',
        'owner_role': 'launchpad-platform-security-reviewer',
        'owner_signature': 'reviewer <reviewer@example.invalid> 2026-11-24',
        'signed_on': '2026-11-24',
        'expires_on': '2027-05-01',
        'source_revision': REVISION,
        'digest_pending': True,
        'rationale': 'Every listed advisory is present only in a pinned vendor '
                     'CLI or an RPM with no errata; none is reachable from the lab path.',
        'accepted': [{
            'id': 'CVE-example',
            'package': 'example-package',
            'severity': 'High',
            'rationale': 'Reviewed: unreachable from the participant path.',
        }],
    }
    record.update(overrides)
    return record


def _candidate(matches=(), *, acceptance=None, component='terminal',
               source_revision=REVISION, today=TODAY):
    return _gate().summarize(
        {**_image_report(), 'matches': list(matches)},
        component=component,
        expected_image='example.invalid/candidate:git-test',
        expected_image_id='sha256:' + 'a' * 64,
        acceptance=_acceptance() if acceptance is None else acceptance,
        source_revision=source_revision,
        today=today,
    )


def test_signed_acceptance_subtracts_only_the_enumerated_findings():
    result = _candidate([_match()])
    assert result['staging_security_gate'] == 'PASS-SCAN-ONLY'
    assert result['risk_acceptance'] == 'GRANTED'
    assert result['gate_basis'] == 'SIGNED-ACCEPTANCE'
    assert result['high_matches'] == 1
    assert result['accepted_high_matches'] == 1
    assert result['unaccepted_high_matches'] == 0
    assert result['platform_staging_qualified'] is False
    assert result['acceptance']['digest_binding'] == 'PENDING-AT-SIGNING'
    assert result['acceptance']['matched_entries'] == 1
    assert result['acceptance']['unused_entries'] == []


def test_acceptance_without_verified_candidate_image_is_refused():
    with pytest.raises(ValueError, match='verified candidate'):
        _gate().summarize({'matches': [_match()]}, component='terminal',
                          acceptance=_acceptance(), source_revision=REVISION, today=TODAY)


def test_unenumerated_finding_still_blocks_under_an_acceptance():
    result = _candidate([_match(), _match('Critical', identifier='CVE-other')])
    assert result['staging_security_gate'] == 'BLOCKED'
    assert result['risk_acceptance'] == 'APPLIED-INCOMPLETE'
    assert result['gate_basis'] == 'BLOCKING-FINDINGS'
    assert result['accepted_high_matches'] == 1
    assert result['unaccepted_critical_matches'] == 1


def test_acceptance_entry_must_match_package_and_severity():
    record = _acceptance(accepted=[{
        'id': 'CVE-example',
        'package': 'some-other-package',
        'severity': 'High',
        'rationale': 'Wrong package on purpose.',
    }])
    result = _candidate([_match()], acceptance=record)
    assert result['staging_security_gate'] == 'BLOCKED'
    assert result['unaccepted_high_matches'] == 1
    assert result['acceptance']['unused_entries'] == [
        {'id': 'CVE-example', 'package': 'some-other-package', 'severity': 'High'}
    ]


def test_acceptance_cannot_cover_a_scanner_suppression():
    report = {**_image_report(), 'matches': [], 'ignoredMatches': [_match()]}
    result = _gate().summarize(
        report, component='terminal',
        expected_image='example.invalid/candidate:git-test',
        expected_image_id='sha256:' + 'a' * 64,
        acceptance=_acceptance(), source_revision=REVISION, today=TODAY,
    )
    assert result['suppressed_high_matches'] == 1
    assert result['staging_security_gate'] == 'BLOCKED'
    assert result['risk_acceptance'] == 'APPLIED-INCOMPLETE'


def test_acceptance_binds_an_exact_digest_when_one_is_named():
    record = _acceptance()
    del record['digest_pending']
    record['candidate_digest'] = 'sha256:' + 'b' * 64
    result = _candidate([_match()], acceptance=record)
    assert result['acceptance']['digest_binding'] == 'BOUND'
    assert result['acceptance']['candidate_digest'] == 'sha256:' + 'b' * 64
    assert result['risk_acceptance'] == 'GRANTED'


def test_acceptance_digest_must_match_the_scanned_image():
    record = _acceptance()
    del record['digest_pending']
    record['candidate_digest'] = 'sha256:' + 'c' * 64
    with pytest.raises(ValueError, match='does not match the scanned image'):
        _candidate([_match()], acceptance=record)


def test_acceptance_must_name_a_digest_or_declare_one_pending():
    record = _acceptance()
    del record['digest_pending']
    with pytest.raises(ValueError, match='digest_pending'):
        _candidate([_match()], acceptance=record)


def test_acceptance_cannot_be_both_bound_and_pending():
    record = _acceptance(candidate_digest='sha256:' + 'b' * 64)
    with pytest.raises(ValueError, match='both'):
        _candidate([_match()], acceptance=record)


def test_expired_acceptance_is_refused():
    with pytest.raises(ValueError, match='expired'):
        _candidate([_match()], acceptance=_acceptance(expires_on='2026-11-30'))


def test_future_dated_acceptance_is_refused():
    with pytest.raises(ValueError, match='future'):
        _candidate([_match()], acceptance=_acceptance(signed_on='2026-12-02'))


def test_acceptance_cannot_outlive_the_review_window():
    with pytest.raises(ValueError, match='180'):
        _candidate([_match()], acceptance=_acceptance(expires_on='2027-12-01'))


def test_acceptance_is_bound_to_the_released_revision():
    with pytest.raises(ValueError, match='different source revision'):
        _candidate([_match()], source_revision='b' * 40)


def test_acceptance_requires_a_source_revision():
    with pytest.raises(ValueError, match='source-revision'):
        _candidate([_match()], source_revision=None)


@pytest.mark.parametrize('field,value', [('id', 'CVE-*'), ('package', 'example-*')])
def test_acceptance_rejects_wildcards(field, value):
    entry = {'id': 'CVE-example', 'package': 'example-package', 'severity': 'High',
             'rationale': 'Reviewed.'}
    entry[field] = value
    with pytest.raises(ValueError, match='wildcard'):
        _candidate([_match()], acceptance=_acceptance(accepted=[entry]))


def test_acceptance_rejects_duplicate_entries():
    entry = {'id': 'CVE-example', 'package': 'example-package', 'severity': 'High',
             'rationale': 'Reviewed.'}
    with pytest.raises(ValueError, match='repeats'):
        _candidate([_match()], acceptance=_acceptance(accepted=[entry, dict(entry)]))


def test_acceptance_requires_a_named_owner_signature():
    with pytest.raises(ValueError, match='owner_signature'):
        _candidate([_match()], acceptance=_acceptance(owner_signature='   '))


def test_acceptance_component_must_match_the_scan():
    with pytest.raises(ValueError, match='component'):
        _candidate([_match()], component='backend')


@pytest.mark.parametrize('field,value', [('schema', 'launchpad/other/v1'),
                                        ('status', 'ACCEPTED')])
def test_acceptance_schema_and_status_are_exact(field, value):
    with pytest.raises(ValueError):
        _candidate([_match()], acceptance=_acceptance(**{field: value}))


def test_acceptance_entries_that_no_longer_match_are_reported_not_fatal():
    result = _candidate([_match('Medium')])
    assert result['staging_security_gate'] == 'PASS-SCAN-ONLY'
    assert result['risk_acceptance'] == 'GRANTED'
    assert result['gate_basis'] == 'CLEAN-SCAN'
    assert result['acceptance']['matched_entries'] == 0
    assert result['acceptance']['unused_entries'] == [
        {'id': 'CVE-example', 'package': 'example-package', 'severity': 'High'}
    ]


def test_absence_of_acceptance_keeps_the_gate_fail_closed():
    result = _gate().summarize(
        {**_image_report(), 'matches': [_match()]}, component='terminal',
        expected_image='example.invalid/candidate:git-test',
        expected_image_id='sha256:' + 'a' * 64, today=TODAY,
    )
    assert result['staging_security_gate'] == 'BLOCKED'
    assert result['risk_acceptance'] == 'NOT-GRANTED'
    assert result['gate_basis'] == 'BLOCKING-FINDINGS'
    assert result['acceptance'] is None


def test_cli_applies_a_signed_acceptance_and_retains_its_hash(tmp_path):
    import hashlib

    report = tmp_path / 'inventory.json'
    report.write_text(json.dumps({**_image_report(), 'matches': [_match()]}))
    acceptance = tmp_path / 'acceptance.json'
    raw = json.dumps(_acceptance()).encode()
    acceptance.write_bytes(raw)
    process = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/check_backend_staging_security.py'), str(report),
         '--component', 'terminal', '--expected-image', 'example.invalid/candidate:git-test',
         '--expected-image-id', 'sha256:' + 'a' * 64, '--acceptance', str(acceptance),
         '--source-revision', REVISION],
        check=False, capture_output=True, text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    decision = json.loads(process.stdout)
    assert decision['risk_acceptance'] == 'GRANTED'
    assert decision['source_revision'] == REVISION
    assert decision['acceptance_sha256'] == hashlib.sha256(raw).hexdigest()


def test_cli_reads_a_yaml_acceptance(tmp_path):
    import yaml

    report = tmp_path / 'inventory.json'
    report.write_text(json.dumps({**_image_report(), 'matches': [_match()]}))
    acceptance = tmp_path / 'acceptance.yaml'
    acceptance.write_text(yaml.safe_dump(_acceptance(), sort_keys=False))
    process = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/check_backend_staging_security.py'), str(report),
         '--component', 'terminal', '--expected-image', 'example.invalid/candidate:git-test',
         '--expected-image-id', 'sha256:' + 'a' * 64, '--acceptance', str(acceptance),
         '--source-revision', REVISION],
        check=False, capture_output=True, text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert json.loads(process.stdout)['risk_acceptance'] == 'GRANTED'


def test_cli_refuses_an_acceptance_without_a_source_revision(tmp_path):
    report = tmp_path / 'inventory.json'
    report.write_text(json.dumps(_image_report()))
    acceptance = tmp_path / 'acceptance.json'
    acceptance.write_text(json.dumps(_acceptance()))
    process = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/check_backend_staging_security.py'), str(report),
         '--component', 'terminal', '--expected-image', 'example.invalid/candidate:git-test',
         '--expected-image-id', 'sha256:' + 'a' * 64, '--acceptance', str(acceptance)],
        check=False, capture_output=True, text=True,
    )
    assert process.returncode == 2
    assert json.loads(process.stdout)['staging_security_gate'] == 'INVALID'


def test_acceptance_requires_a_scope_rationale():
    record = _acceptance()
    del record['rationale']
    with pytest.raises(ValueError, match='rationale'):
        _candidate([_match()], acceptance=record)


def test_acceptance_entry_rationale_is_optional_but_typed():
    entry = {'id': 'CVE-example', 'package': 'example-package', 'severity': 'High'}
    result = _candidate([_match()], acceptance=_acceptance(accepted=[entry]))
    assert result['risk_acceptance'] == 'GRANTED'
    assert result['acceptance']['accepted_entries'] == 1
    assert result['acceptance']['rationale'].startswith('Every listed advisory')


@pytest.mark.parametrize('scope,record_update', [
    ('record', {'candidate_digset': 'sha256:' + 'b' * 64}),
    ('entry', {'accepted': [{'id': 'CVE-example', 'package': 'example-package',
                             'severity': 'High', 'rational': 'typo'}]}),
])
def test_acceptance_rejects_unknown_fields_instead_of_ignoring_them(scope, record_update):
    with pytest.raises(ValueError, match='unknown fields'):
        _candidate([_match()], acceptance=_acceptance(**record_update))
