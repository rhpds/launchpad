"""Fail closed on full Grype High/Critical inventory; never grant platform staging."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def summarize(report: dict, *, component: str = 'backend') -> dict:
    if component not in {'backend', 'terminal'}:
        raise ValueError('Unsupported image component')
    if not isinstance(report, dict) or not isinstance(report.get("matches"), list):
        raise ValueError("A complete Grype matches inventory is required")  # noqa: TRY004
    configuration = report.get("descriptor", {}).get("configuration", {})
    if configuration.get("only-fixed") or configuration.get("only-notfixed"):
        raise ValueError("A filtered scan cannot qualify staging")
    ignored = report.get("ignoredMatches", [])
    if not isinstance(ignored, list):
        raise ValueError("Malformed suppressed vulnerability inventory")  # noqa: TRY004
    counts: Counter[str] = Counter()
    states: Counter[str] = Counter()
    identifiers: set[str] = set()
    suppressed: Counter[str] = Counter()
    for match, is_suppressed in (
        [(item, False) for item in report["matches"]]
        + [(item, True) for item in ignored]
    ):
        if not isinstance(match, dict) or not isinstance(match.get("vulnerability"), dict):
            raise ValueError("Malformed vulnerability inventory")  # noqa: TRY004
        vulnerability = match["vulnerability"]
        severity = vulnerability.get("severity")
        identifier = vulnerability.get("id")
        if severity not in {"Critical", "High", "Medium", "Low", "Negligible", "Unknown"}:
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
    blocked = any(
        inventory[severity]
        for inventory in (counts, suppressed)
        for severity in ("High", "Critical", "Unknown")
    )
    return {
        "schema": f"launchpad/{component}-staging-security/v1",
        "staging_security_gate": "BLOCKED" if blocked else "PASS-SCAN-ONLY",
        "platform_staging_qualified": False,
        "high_matches": counts["High"],
        "critical_matches": counts["Critical"],
        "suppressed_high_matches": suppressed["High"],
        "suppressed_critical_matches": suppressed["Critical"],
        "suppressed_unrated_matches": suppressed["Unknown"],
        "unrated_matches": counts["Unknown"],
        "distinct_high_critical_ids": len(identifiers),
        "high_critical_fix_states": dict(sorted(states.items())),
        "risk_acceptance": "NOT-GRANTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument('--component', choices=('backend', 'terminal'), default='backend')
    args = parser.parse_args()
    try:
        raw = args.report.read_bytes()
        report = json.loads(raw)
        result = summarize(report, component=args.component)
        result["report_sha256"] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError) as exc:
        print(json.dumps({"staging_security_gate": "INVALID", "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["staging_security_gate"] == "PASS-SCAN-ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
