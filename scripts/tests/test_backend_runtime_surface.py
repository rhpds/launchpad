"""Release contracts for reducing runtime surface without losing platform tools."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_headless_runtime_removes_exact_x11_packages_and_verifies_their_absence():
    text = (ROOT / "backend/Containerfile").read_text()
    smoke = (ROOT / "backend/scripts/runtime_smoke.py").read_text()
    for package in ("libX11", "libX11-common", "libX11-xcb", "libXrender"):
        assert re.search(rf"(?<![\w-]){re.escape(package)}(?![\w-])", text)
        assert f'"{package}"' in smoke
    assert "clean_requirements_on_remove=False" in text
    for tool in ("oc", "helm", "git", "curl", "openssl"):
        assert f'"{tool}"' in smoke


def test_runtime_removes_unused_web_server_without_autoremoving_dependencies():
    text = (ROOT / "backend/Containerfile").read_text()
    assert "clean_requirements_on_remove=False" in text
    assert "httpd-core httpd-devel httpd-filesystem httpd-tools" in text
    assert "mod_ldap mod_lua mod_session mod_ssl" in text
    assert "gd gd-devel" in text
    assert "COPY backend/scripts/ ./scripts/" in text


def test_release_smokes_built_image_before_scan_and_publication():
    workflow = yaml.safe_load((ROOT / ".github/workflows/backend-release.yml").read_text())
    steps = workflow["jobs"]["release"]["steps"]
    names = [step.get("name") for step in steps]
    smoke = next(step for step in steps if step.get("name") == "Verify backend runtime surface")
    assert names.index(smoke["name"]) < names.index("Inventory all candidate vulnerabilities")
    assert names.index(smoke["name"]) < names.index("Publish immutable candidate and record digest")
    assert "--network none" in smoke["run"]
    assert "--read-only" in smoke["run"]
    assert "--user 1001" in smoke["run"]
    assert "runtime_smoke.py" in smoke["run"]


def test_smoke_preserves_platform_dependencies_and_cli_tools():
    text = (ROOT / "backend/scripts/runtime_smoke.py").read_text()
    for name in ("sqlalchemy", "psycopg2", "kubernetes", "celery", "cryptography", "argon2"):
        assert name in text
    for tool in ("oc", "helm", "git", "curl", "openssl"):
        assert f'"{tool}"' in text
    assert "get_ca_certs" in text
    assert "httpd" in text
    assert "check=True" in text


def test_runtime_drops_unused_headers_editors_and_development_packages():
    text = (ROOT / "backend/Containerfile").read_text()
    smoke = (ROOT / "backend/scripts/runtime_smoke.py").read_text()
    for package in (
        "kernel-headers", "python3.11-devel", "expat-devel", "libblkid-devel",
        "libmount-devel", "go-srpm-macros", "qt5-srpm-macros",
        "emacs-filesystem", "vim-filesystem", "vim-minimal", "libX11-devel",
    ):
        assert package in text
        assert f'"{package}"' in smoke
    assert "clean_requirements_on_remove=False" in text


def test_scans_still_collect_after_symbol_failure_but_publication_stays_gated():
    workflow = yaml.safe_load((ROOT / ".github/workflows/backend-release.yml").read_text())
    steps = workflow["jobs"]["release"]["steps"]
    smoke = next(step for step in steps if step.get("name") == "Verify backend runtime surface")
    assert smoke["id"] == "runtime_smoke"
    for name in (
        "Release build cache before security scanning", "Inventory all candidate vulnerabilities",
        "Inventory fixable high and critical vulnerabilities",
    ):
        step = next(step for step in steps if step.get("name") == name)
        assert "!cancelled()" in step["if"]
        assert "steps.runtime_smoke.outcome == 'success'" in step["if"]
        assert step.get("continue-on-error", False) is False
    publish = next(step for step in steps if step.get("name") == "Publish immutable candidate and record digest")
    assert publish["if"] == "${{ inputs.publish }}"


def test_runtime_moves_to_supported_python_312_with_explicit_smoke_assertion():
    text = (ROOT / "backend/Containerfile").read_text()
    smoke = (ROOT / "backend/scripts/runtime_smoke.py").read_text()
    assert "FROM registry.access.redhat.com/ubi9/python-312:latest" in text
    assert "python3.12-devel" in text
    assert "sys.version_info[:2] != (3, 12)" in smoke


def test_candidate_interpreter_runs_regressions_without_shipping_test_tools():
    workflow = yaml.safe_load((ROOT / ".github/workflows/backend-release.yml").read_text())
    steps = workflow["jobs"]["release"]["steps"]
    test = next(step for step in steps if step.get("name") == "Verify regressions under the candidate interpreter")
    assert "backend/Containerfile.test" in test["run"]
    assert "--network none" in test["run"]
    assert "--read-only" in test["run"]
    assert "test_staging_access_cleanup_gaps.py" in test["run"]
    assert "$GITHUB_WORKSPACE/backend/tests:/workspace/backend/tests:ro" in test["run"]
    assert "$GITHUB_WORKSPACE:/workspace" not in test["run"]
    assert "pytest" not in (ROOT / "backend/Containerfile").read_text()
    assert "pytest==8.4.2" in (ROOT / "backend/Containerfile.test").read_text()
