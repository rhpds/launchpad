"""Inventory named Go client symbols for review; never declare non-applicability."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SURFACES = {
    "distribution-proxy": ("github.com/distribution/distribution/v3/registry/proxy.",),
    "distribution-redis-cache": (
        "github.com/distribution/distribution/v3/registry/storage/cache/redis.",
    ),
    "buildkit-git-source": ("github.com/moby/buildkit/source/git.",),
    "buildkit-solver": ("github.com/moby/buildkit/solver/",),
    "buildkit-gateway": ("github.com/moby/buildkit/frontend/gateway/",),
    "archive-extraction": ("github.com/moby/go-archive.",),
}


def inventory(text: str) -> dict:
    symbols = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*(?:[0-9a-fA-F]+\s+)?[A-Za-z?]\s+(\S.*)", line)
        if not match:
            raise ValueError("Unrecognized Go nm output; cannot infer symbol absence")
        symbols.append(match.group(1).strip())
    if not {"main.main", "runtime.main"}.issubset(symbols):
        raise ValueError("Client entry symbols missing; inventory cannot be trusted")
    return {
        "schema": "launchpad/backend-client-symbol-inventory/v1",
        "symbols_count": len(symbols),
        "surfaces": {
            name: {
                "named_symbols_present": bool(selected := [
                    symbol for symbol in symbols if symbol.startswith(prefixes)
                ]),
                "matching_count": len(selected),
                "examples": sorted(selected)[:10],
            }
            for name, prefixes in SURFACES.items()
        },
        "not_affected_declared": False,
        "staging_qualified": False,
        "risk_acceptance": "NOT-GRANTED",
        "limitations": [
            "Named-symbol absence alone does not exclude inlined code or prove unreachability.",
            "Package-prefix presence does not prove the vulnerable function is invoked.",
            "Review exact source, advisory call sites, inputs, and runtime before any disposition.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", type=Path)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
            raise ValueError("Exact source revision required")
        raw = args.symbols.read_bytes()
        report = inventory(raw.decode("utf-8"))
        report["symbols_sha256"] = hashlib.sha256(raw).hexdigest()
        report["binary_sha256"] = hashlib.sha256(args.binary.read_bytes()).hexdigest()
        report["source_revision"] = args.source_revision
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
