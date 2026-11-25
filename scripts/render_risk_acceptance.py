#!/usr/bin/env python3
"""Render a launchpad/risk-acceptance/v1 record from a measured Grype report.

This script does not make the decision. It only transcribes the exact
advisory/package/severity triples that the gate would otherwise block on, so
the reviewer signs a precise scope instead of retyping it. The owner role,
signature, rationale, validity window and revision are all required arguments,
and the emitted record is validated with the gate's own validator before it is
written, so this cannot produce a file the gate would silently reject.

Every blocking finding in ``matches`` is enumerated. Suppressions are refused:
the gate never lets a risk acceptance cover a match the scanner was told not to
report, so a report with ``ignoredMatches`` cannot yield a passing record.

Examples:

    python3 scripts/render_risk_acceptance.py vulnerability-report.json \
      --component terminal \
      --owner-role launchpad-platform-security-reviewer \
      --owner-signature 'jkershaw, 2026-11-24' \
      --signed-on 2026-11-24 --expires-on 2027-02-22 \
      --source-revision "$(git rev-parse HEAD)" \
      --rationale 'Residual advisories live only in pinned Red Hat CLIs; none is reachable.' \
      --digest-pending --output evidence/security/terminal-risk-acceptance.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_backend_staging_security import (  # noqa: E402
    ACCEPTANCE_SCHEMA,
    ACCEPTANCE_STATUS,
    BLOCKING_SEVERITIES,
    validate_acceptance,
)

# Order the rendered list for review, most severe first. Deriving this from
# BLOCKING_SEVERITIES would put High ahead of Critical, because that tuple is
# ordered for reporting, not for reading.
_RENDER_SEVERITY_ORDER = ('Critical', 'High', 'Unknown')
if set(_RENDER_SEVERITY_ORDER) != set(BLOCKING_SEVERITIES):  # pragma: no cover
    raise RuntimeError('Render order must cover exactly the blocking severities')
_SEVERITY_ORDER = {severity: rank for rank, severity in enumerate(_RENDER_SEVERITY_ORDER)}


def _package_name(match: dict) -> str | None:
    artifact = match.get('artifact')
    name = artifact.get('name') if isinstance(artifact, dict) else None
    return name if isinstance(name, str) and name else None


def build_record(report: dict, *, component: str, owner_role: str, owner_signature: str,
                 signed_on: str, expires_on: str, source_revision: str, rationale: str,
                 report_sha256: str, candidate_digest: str | None,
                 digest_pending: bool) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get('matches'), list):
        raise ValueError('A complete Grype matches inventory is required')
    suppressed = report.get('ignoredMatches') or []
    if suppressed:
        raise ValueError(
            'Refusing to render a risk acceptance over a report with suppressed matches: '
            'the gate never lets an acceptance cover a scanner suppression'
        )
    triples: set[tuple[str, str, str]] = set()
    unnamed: list[str] = []
    for match in report['matches']:
        vulnerability = match.get('vulnerability') if isinstance(match, dict) else None
        if not isinstance(vulnerability, dict):
            raise ValueError('Malformed vulnerability inventory')
        severity = vulnerability.get('severity')
        identifier = vulnerability.get('id')
        if severity not in BLOCKING_SEVERITIES:
            continue
        if not isinstance(identifier, str) or not identifier:
            raise ValueError('Missing vulnerability identifier')
        package = _package_name(match)
        if package is None:
            unnamed.append(identifier)
            continue
        triples.add((identifier, package, severity))
    if unnamed:
        raise ValueError(
            'Cannot enumerate findings without a package name: ' + ', '.join(sorted(set(unnamed)))
        )
    if not triples:
        raise ValueError('The report has no High, Critical or Unrated findings to accept')
    accepted = [
        {'id': identifier, 'package': package, 'severity': severity}
        for identifier, package, severity in sorted(
            triples, key=lambda triple: (_SEVERITY_ORDER[triple[2]], triple[1], triple[0])
        )
    ]
    record = {
        'schema': ACCEPTANCE_SCHEMA,
        'component': component,
        'status': ACCEPTANCE_STATUS,
        'owner_role': owner_role,
        'owner_signature': owner_signature,
        'signed_on': signed_on,
        'expires_on': expires_on,
        'source_revision': source_revision,
        'rationale': rationale,
        'report_sha256': report_sha256,
        'accepted': accepted,
    }
    if candidate_digest is not None:
        record['candidate_digest'] = candidate_digest
    elif digest_pending:
        record['digest_pending'] = True
    return record


def render(record: dict, suffix: str) -> str:
    if suffix == '.yaml' or suffix == '.yml':
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - exercise via CLI on a bare interpreter
            raise ValueError('YAML output needs PyYAML; write a .json record instead') from exc
        return yaml.safe_dump(record, sort_keys=False, width=100)
    return json.dumps(record, indent=2) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('report', type=Path)
    parser.add_argument('--component', choices=('backend', 'terminal'), required=True)
    parser.add_argument('--owner-role', required=True)
    parser.add_argument('--owner-signature', required=True)
    parser.add_argument('--signed-on', required=True)
    parser.add_argument('--expires-on', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--rationale', required=True)
    binding = parser.add_mutually_exclusive_group(required=True)
    binding.add_argument('--candidate-digest')
    binding.add_argument('--digest-pending', action='store_true')
    parser.add_argument('--output', type=Path,
                        help='Destination file; .json (default) or .yaml/.yml. Omit for stdout.')
    args = parser.parse_args()
    try:
        raw = args.report.read_bytes()
        report = json.loads(raw)
        target = (report.get('source') or {}).get('target') or {}
        report_digest = target.get('manifestDigest') if isinstance(target, dict) else None
        if args.candidate_digest and report_digest and args.candidate_digest != report_digest:
            raise ValueError('--candidate-digest does not match the digest recorded in the report')
        record = build_record(
            report, component=args.component, owner_role=args.owner_role,
            owner_signature=args.owner_signature, signed_on=args.signed_on,
            expires_on=args.expires_on, source_revision=args.source_revision,
            rationale=args.rationale, report_sha256=hashlib.sha256(raw).hexdigest(),
            candidate_digest=args.candidate_digest, digest_pending=args.digest_pending,
        )
        validate_acceptance(
            record, component=args.component, source_revision=args.source_revision,
            manifest_digest=args.candidate_digest or report_digest,
            today=dt.datetime.now(dt.timezone.utc).date(),
        )
        rendered = render(record, args.output.suffix if args.output else '.json')
    except (OSError, ValueError) as exc:
        print(f'render_risk_acceptance: {exc}', file=sys.stderr)
        return 2
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
        print(f'wrote {args.output} with {len(record["accepted"])} accepted findings')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
