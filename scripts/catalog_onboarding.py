#!/usr/bin/env python3
"""Validate and render repository-native Launchpad catalog onboarding contracts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.catalog_onboarding import (
    build_catalog_item,
    load_intake,
    validate_intake,
)


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _fetch_source(repo_url: str, revision: str, destination: Path) -> None:
    destination.mkdir(parents=True)
    _run(["git", "init", "--quiet"], cwd=destination)
    _run(["git", "remote", "add", "origin", repo_url], cwd=destination)
    _run(["git", "fetch", "--quiet", "--depth", "1", "origin", revision], cwd=destination)
    _run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=destination)
    actual = _run(["git", "rev-parse", "HEAD"], cwd=destination).stdout.strip()
    if actual != revision:
        raise RuntimeError(
            f"Fetched {repo_url} at {actual}, expected immutable revision {revision}"
        )


def _render(args: argparse.Namespace) -> int:
    intake = load_intake(args.intake)
    rendered = yaml.safe_dump(build_catalog_item(intake), sort_keys=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered)
    else:
        print(rendered, end="")
    return 0


def _validate(args: argparse.Namespace) -> int:
    intake = load_intake(args.intake)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    showroom_dir = Path(args.showroom_dir).resolve() if args.showroom_dir else None
    workload_dir = Path(args.workload_dir).resolve() if args.workload_dir else None

    try:
        if args.fetch:
            if showroom_dir or workload_dir:
                raise ValueError("--fetch cannot be combined with local source directories")
            temporary = tempfile.TemporaryDirectory(prefix="launchpad-catalog-onboarding-")
            source_root = Path(temporary.name)
            showroom_dir = source_root / "showroom"
            workload_dir = source_root / "workload"
            _fetch_source(
                intake["sources"]["showroom"]["repo_url"],
                intake["sources"]["showroom"]["revision"],
                showroom_dir,
            )
            _fetch_source(
                intake["sources"]["workload"]["repo_url"],
                intake["sources"]["workload"]["revision"],
                workload_dir,
            )

        catalog = yaml.safe_load(Path(args.catalog).read_text()) if args.catalog else None
        report = validate_intake(
            intake,
            showroom_dir=showroom_dir,
            workload_dir=workload_dir,
            catalog=catalog,
        )

        if args.build_showroom:
            if showroom_dir is None:
                raise ValueError("--build-showroom requires --fetch or --showroom-dir")
            antora = Path(args.antora_bin).resolve() if args.antora_bin else None
            executable = str(antora) if antora else "antora"
            playbook = intake["sources"]["showroom"]["playbook"]
            try:
                _run([executable, "--fetch", playbook], cwd=showroom_dir)
                report["checks"]["showroom_build"] = "pass"
            except (OSError, subprocess.CalledProcessError) as exc:
                report["checks"]["showroom_build"] = "fail"
                report["validation_status"] = "fail"
                report["activation_status"] = "blocked"
                detail = getattr(exc, "stderr", None) or str(exc)
                report["errors"].append(f"Antora build failed: {detail.strip()}")
        else:
            report["checks"]["showroom_build"] = "not-run"

        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.report:
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            Path(args.report).write_text(rendered)
        print(rendered, end="")
        return 0 if report["validation_status"] == "pass" else 1
    finally:
        if temporary is not None:
            temporary.cleanup()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render and validate Launchpad catalog onboarding contracts"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="render the generated draft catalog YAML")
    render.add_argument("intake", type=Path)
    render.add_argument("--output", type=Path)
    render.set_defaults(handler=_render)

    validate = subparsers.add_parser(
        "validate", help="validate intake, source repositories, build, and catalog drift"
    )
    validate.add_argument("intake", type=Path)
    validate.add_argument("--catalog", type=Path)
    validate.add_argument("--fetch", action="store_true")
    validate.add_argument("--showroom-dir", type=Path)
    validate.add_argument("--workload-dir", type=Path)
    validate.add_argument("--build-showroom", action="store_true")
    validate.add_argument("--antora-bin", type=Path)
    validate.add_argument("--report", type=Path)
    validate.set_defaults(handler=_validate)
    return parser


def main() -> int:
    # Ensure subprocesses do not inherit a repository-local Git override that
    # could redirect source fetches in a contributor environment.
    os.environ.pop("GIT_DIR", None)
    os.environ.pop("GIT_WORK_TREE", None)
    args = _parser().parse_args()
    try:
        return args.handler(args)
    except (
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"catalog onboarding failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
