"""Fail closed on the full Grype inventory; only a signed scope can subtract from it.

An image clears this gate in exactly one of two ways: its complete, unfiltered
Grype inventory carries no High, Critical or Unrated finding at all, or a
reviewed, time-bounded risk acceptance enumerates every remaining blocking
finding by exact advisory, package and severity.

Two properties are deliberate:

* A scanner suppression is never evidence of review. Matches in
  ``ignoredMatches`` keep counting against the gate and a risk acceptance cannot
  cover them, because an ignore rule is an instruction not to report a finding,
  not a decision that the finding is acceptable.
* This gate never grants platform staging qualification. A signed acceptance
  changes the release decision, not the qualification state.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ACCEPTANCE_SCHEMA = 'launchpad/risk-acceptance/v1'
ACCEPTANCE_STATUS = 'ACCEPTED-WITH-SCOPE'
MAX_ACCEPTANCE_DAYS = 180
BLOCKING_SEVERITIES = ('High', 'Critical', 'Unknown')
KNOWN_SEVERITIES = ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown')
_DIGEST_RE = re.compile(r'sha256:[0-9a-f]{64}')
_REVISION_RE = re.compile(r'[0-9a-f]{40}')
_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')
_ACCEPTANCE_KEYS = {
    'schema', 'component', 'status', 'owner_role', 'owner_signature', 'signed_on',
    'expires_on', 'source_revision', 'candidate_digest', 'digest_pending', 'rationale',
    'report_sha256', 'accepted',
}
_ENTRY_KEYS = {'id', 'package', 'severity', 'rationale'}


def _utc_today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def _required_text(record: dict, field: str, *, context: str = 'Acceptance') -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{context} {field} is required')
    return value.strip()


def _as_date(value: object, field: str) -> dt.date:
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise ValueError(f'Acceptance {field} must be an ISO date (YYYY-MM-DD)')
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:  # impossible after the regex, kept fail-closed
        raise ValueError(f'Acceptance {field} is not a real date') from exc


def load_acceptance(path: Path) -> dict:
    """Read a risk-acceptance record. YAML needs PyYAML; JSON needs nothing."""
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.json':
        return json.loads(text)
    try:
        import yaml
    except ImportError as exc:
        raise ValueError(
            'A YAML risk acceptance needs PyYAML; supply a .json record instead'
        ) from exc
    record = yaml.safe_load(text)
    if not isinstance(record, dict):
        raise ValueError('Acceptance record must be a mapping')  # noqa: TRY004
    return record


def validate_acceptance(record: dict, *, component: str, source_revision: str | None,
                        manifest_digest: str | None, today: dt.date) -> dict:
    """Validate a reviewed acceptance and return its normalized form.

    The bound fields are the point of the record: the same component, the same
    candidate image (by digest, or explicitly pending when the image does not
    exist yet), the revision being released, a live expiry and an exhaustive
    list of exact advisories. Anything less fails closed.
    """
    if not isinstance(record, dict):
        raise ValueError('Acceptance record must be a mapping')  # noqa: TRY004
    unknown = set(record) - _ACCEPTANCE_KEYS
    if unknown:
        raise ValueError(f'Acceptance has unknown fields: {sorted(unknown)}')
    if record.get('schema') != ACCEPTANCE_SCHEMA:
        raise ValueError(f'Acceptance schema must be {ACCEPTANCE_SCHEMA}')
    if record.get('component') != component:
        raise ValueError('Acceptance component does not match the scanned image')
    if record.get('status') != ACCEPTANCE_STATUS:
        raise ValueError(f'Acceptance status must be {ACCEPTANCE_STATUS}')
    owner_role = _required_text(record, 'owner_role')
    owner_signature = _required_text(record, 'owner_signature')
    rationale = _required_text(record, 'rationale')
    signed_on = _as_date(record.get('signed_on'), 'signed_on')
    expires_on = _as_date(record.get('expires_on'), 'expires_on')
    if signed_on > today:
        raise ValueError('Acceptance is signed in the future')
    if expires_on < signed_on:
        raise ValueError('Acceptance expires before it was signed')
    if expires_on < today:
        raise ValueError('Acceptance has expired')
    if (expires_on - signed_on).days > MAX_ACCEPTANCE_DAYS:
        raise ValueError(f'Acceptance may not stay valid for more than {MAX_ACCEPTANCE_DAYS} days')
    accepted_revision = record.get('source_revision')
    if not isinstance(accepted_revision, str) or not _REVISION_RE.fullmatch(accepted_revision):
        raise ValueError('Acceptance source_revision must be a 40-character lowercase hex revision')
    if not source_revision:
        raise ValueError('--source-revision is required to apply an acceptance')
    if accepted_revision != source_revision:
        raise ValueError('Acceptance was signed for a different source revision')
    digest = record.get('candidate_digest')
    pending = record.get('digest_pending')
    if digest is not None:
        if pending is not None:
            raise ValueError('Acceptance cannot both name a digest and declare it pending')
        if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
            raise ValueError('Acceptance candidate_digest must be a sha256 digest')
        if digest != manifest_digest:
            raise ValueError('Acceptance candidate_digest does not match the scanned image')
        digest_binding = 'BOUND'
    else:
        if pending is not True:
            raise ValueError('Acceptance must name candidate_digest or set digest_pending: true')
        digest_binding = 'PENDING-AT-SIGNING'
    entries = record.get('accepted')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Acceptance must enumerate the accepted findings')
    report_sha256 = record.get('report_sha256')
    if report_sha256 is not None and (
        not isinstance(report_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', report_sha256)
    ):
        raise ValueError('Acceptance report_sha256 must be a sha256 hex digest')
    accepted: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Acceptance entries must be mappings')  # noqa: TRY004
        unknown_entry = set(entry) - _ENTRY_KEYS
        if unknown_entry:
            raise ValueError(f'Acceptance entry has unknown fields: {sorted(unknown_entry)}')
        identifier = _required_text(entry, 'id', context='Acceptance entry')
        package = _required_text(entry, 'package', context='Acceptance entry')
        entry_rationale = entry.get('rationale')
        if entry_rationale is not None:
            entry_rationale = _required_text(entry, 'rationale', context='Acceptance entry')
        severity = entry.get('severity')
        if severity not in BLOCKING_SEVERITIES:
            raise ValueError(f'Acceptance entry severity must be one of {BLOCKING_SEVERITIES}')
        if any(character in identifier or character in package for character in '*?'):
            raise ValueError('Acceptance entries must name exact advisories and packages, not wildcards')
        key = (identifier, package, severity)
        if key in seen:
            raise ValueError(f'Acceptance repeats {identifier}/{package}/{severity}')
        seen.add(key)
        accepted.append({'id': identifier, 'package': package, 'severity': severity,
                         'rationale': entry_rationale})
    return {
        'schema': ACCEPTANCE_SCHEMA,
        'status': ACCEPTANCE_STATUS,
        'owner_role': owner_role,
        'owner_signature': owner_signature,
        'signed_on': signed_on.isoformat(),
        'expires_on': expires_on.isoformat(),
        'source_revision': accepted_revision,
        'candidate_digest': digest,
        'digest_binding': digest_binding,
        'rationale': rationale,
        'report_sha256': report_sha256,
        'accepted_count': len(accepted),
        'accepted': accepted,
    }


def summarize(report: dict, *, component: str = 'backend',
              expected_image: str | None = None, expected_image_id: str | None = None,
              acceptance: dict | None = None, source_revision: str | None = None,
              today: dt.date | None = None) -> dict:
    if component not in {'backend', 'terminal'}:
        raise ValueError('Unsupported image component')
    if not isinstance(report, dict) or not isinstance(report.get("matches"), list):
        raise ValueError("A complete Grype matches inventory is required")  # noqa: TRY004
    descriptor = report.get('descriptor', {})
    if not isinstance(descriptor, dict):
        raise ValueError('Malformed scan descriptor')  # noqa: TRY004
    configuration = descriptor.get('configuration', {})
    if not isinstance(configuration, dict):
        raise ValueError('Malformed scan configuration')  # noqa: TRY004
    if any(configuration.get(setting) for setting in (
        'only-fixed', 'only-notfixed', 'ignore-wontfix', 'exclude',
    )):
        raise ValueError("A filtered scan cannot qualify staging")
    identity: dict = {'candidate_identity_verified': False}
    if expected_image is not None or expected_image_id is not None:
        if not expected_image or not re.fullmatch(r'sha256:[0-9a-f]{64}', expected_image_id or ''):
            raise ValueError('Expected candidate image and SHA256 image ID are required together')
        source = report.get('source')
        if not isinstance(source, dict) or source.get('type') != 'image':
            raise ValueError('A candidate image scan is required')
        target = source.get('target')
        if not isinstance(target, dict):
            raise ValueError('Missing candidate image identity')
        if descriptor.get('name') != 'grype' or 'configuration' not in descriptor:
            raise ValueError('A complete Grype scan descriptor is required')
        if target.get('userInput') != expected_image or target.get('imageID') != expected_image_id:
            raise ValueError('Scan does not match the candidate image')
        digest = target.get('manifestDigest')
        if not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError('Missing candidate manifest digest')
        identity = {'candidate_identity_verified': True, 'image_reference': expected_image,
                    'image_id': expected_image_id, 'manifest_digest': digest}
    validated = None
    accepted_keys: set[tuple[str, str, str]] = set()
    if acceptance is not None:
        if not identity.get('candidate_identity_verified'):
            raise ValueError('A risk acceptance requires a verified candidate image')
        validated = validate_acceptance(
            acceptance, component=component, source_revision=source_revision,
            manifest_digest=identity.get('manifest_digest'), today=today or _utc_today(),
        )
        accepted_keys = {(entry['id'], entry['package'], entry['severity'])
                         for entry in validated['accepted']}
    ignored = report.get("ignoredMatches", [])
    if not isinstance(ignored, list):
        raise ValueError("Malformed suppressed vulnerability inventory")  # noqa: TRY004
    counts: Counter[str] = Counter()
    states: Counter[str] = Counter()
    identifiers: set[str] = set()
    suppressed: Counter[str] = Counter()
    accepted: Counter[str] = Counter()
    unaccepted: Counter[str] = Counter()
    matched_keys: set[tuple[str, str, str]] = set()
    for match, is_suppressed in (
        [(item, False) for item in report["matches"]]
        + [(item, True) for item in ignored]
    ):
        if not isinstance(match, dict) or not isinstance(match.get("vulnerability"), dict):
            raise ValueError("Malformed vulnerability inventory")  # noqa: TRY004
        vulnerability = match["vulnerability"]
        severity = vulnerability.get("severity")
        identifier = vulnerability.get("id")
        if severity not in KNOWN_SEVERITIES:
            raise ValueError("Missing or unsupported vulnerability severity")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("Missing vulnerability identifier")
        (suppressed if is_suppressed else counts)[severity] += 1
        if severity in {"High", "Critical"}:
            identifiers.add(identifier)
            fix = vulnerability.get("fix") or {}
            if not isinstance(fix, dict):
                raise ValueError("Malformed fix inventory")
            states[str(fix.get("state") or "unspecified")] += 1
        if severity in BLOCKING_SEVERITIES and not is_suppressed:
            artifact = match.get("artifact")
            package = artifact.get("name") if isinstance(artifact, dict) else None
            key = (identifier, package, severity)
            if key in accepted_keys:
                accepted[severity] += 1
                matched_keys.add(key)
            else:
                unaccepted[severity] += 1
    # A suppression is an instruction not to report a finding, never a review.
    blocked = any(
        inventory[severity]
        for inventory in (unaccepted, suppressed)
        for severity in BLOCKING_SEVERITIES
    )
    if validated is None:
        risk_acceptance = 'NOT-GRANTED'
    elif blocked:
        risk_acceptance = 'APPLIED-INCOMPLETE'
    else:
        risk_acceptance = 'GRANTED'
    if blocked:
        gate_basis = 'BLOCKING-FINDINGS'
    elif validated is not None and matched_keys:
        gate_basis = 'SIGNED-ACCEPTANCE'
    else:
        gate_basis = 'CLEAN-SCAN'
    acceptance_block = None
    if validated is not None:
        acceptance_block = {
            'schema': validated['schema'],
            'status': validated['status'],
            'owner_role': validated['owner_role'],
            'owner_signature': validated['owner_signature'],
            'signed_on': validated['signed_on'],
            'expires_on': validated['expires_on'],
            'source_revision': validated['source_revision'],
            'candidate_digest': validated['candidate_digest'],
            'digest_binding': validated['digest_binding'],
            'rationale': validated['rationale'],
            'report_sha256': validated['report_sha256'],
            'accepted_entries': validated['accepted_count'],
            'matched_entries': len(matched_keys),
            # Entries that no longer match are reported, not fatal: an image that
            # shrank its finding set must not reopen review, but a stale record
            # has to be visible in the evidence.
            'unused_entries': [
                {'id': identifier, 'package': package, 'severity': severity}
                for identifier, package, severity in sorted(accepted_keys - matched_keys)
            ],
        }
    return {
        "schema": f"launchpad/{component}-staging-security/v1",
        "staging_security_gate": "BLOCKED" if blocked else "PASS-SCAN-ONLY",
        "platform_staging_qualified": False,
        "source_revision": source_revision,
        "high_matches": counts["High"],
        "critical_matches": counts["Critical"],
        "suppressed_high_matches": suppressed["High"],
        "suppressed_critical_matches": suppressed["Critical"],
        "suppressed_unrated_matches": suppressed["Unknown"],
        "unrated_matches": counts["Unknown"],
        "accepted_high_matches": accepted["High"],
        "accepted_critical_matches": accepted["Critical"],
        "accepted_unrated_matches": accepted["Unknown"],
        "unaccepted_high_matches": unaccepted["High"],
        "unaccepted_critical_matches": unaccepted["Critical"],
        "unaccepted_unrated_matches": unaccepted["Unknown"],
        "distinct_high_critical_ids": len(identifiers),
        "high_critical_fix_states": dict(sorted(states.items())),
        "risk_acceptance": risk_acceptance,
        "gate_basis": gate_basis,
        "acceptance": acceptance_block,
        **identity,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument('--component', choices=('backend', 'terminal'), default='backend')
    parser.add_argument('--expected-image')
    parser.add_argument('--expected-image-id')
    parser.add_argument('--acceptance', type=Path,
                        help='Signed launchpad/risk-acceptance/v1 record (YAML or JSON)')
    parser.add_argument('--source-revision',
                        help='40-character revision the candidate was built from')
    args = parser.parse_args()
    try:
        if args.acceptance is not None and not args.source_revision:
            raise ValueError('--source-revision is required with --acceptance')
        if args.source_revision is not None and not _REVISION_RE.fullmatch(args.source_revision):
            raise ValueError('--source-revision must be a 40-character lowercase hex revision')
        raw = args.report.read_bytes()
        report = json.loads(raw)
        acceptance = load_acceptance(args.acceptance) if args.acceptance else None
        result = summarize(report, component=args.component, expected_image=args.expected_image,
                           expected_image_id=args.expected_image_id, acceptance=acceptance,
                           source_revision=args.source_revision)
        result["report_sha256"] = hashlib.sha256(raw).hexdigest()
        if args.acceptance is not None:
            result['acceptance_file'] = str(args.acceptance)
            result['acceptance_sha256'] = hashlib.sha256(args.acceptance.read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        print(json.dumps({"staging_security_gate": "INVALID", "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["staging_security_gate"] == "PASS-SCAN-ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
