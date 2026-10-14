import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location(
        "client_symbols", ROOT / "scripts/inventory_backend_client_symbols.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = "001 T main.main\n002 T runtime.main\n"


def test_module_presence_does_not_imply_vulnerable_server_symbols():
    result = _module().inventory(BASE + "003 T github.com/distribution/distribution/v3/registry/client.New\n")
    assert result["surfaces"]["distribution-proxy"]["named_symbols_present"] is False
    assert result["surfaces"]["distribution-redis-cache"]["named_symbols_present"] is False
    assert result["not_affected_declared"] is False
    assert result["staging_qualified"] is False


def test_vulnerable_subsystem_symbols_are_reported_not_waived():
    text = BASE + (
        "003 T github.com/distribution/distribution/v3/registry/proxy.getAuthURLs\n"
        "004 T github.com/moby/buildkit/source/git.NewSource\n"
        "005 T github.com/moby/go-archive.Unpack\n"
    )
    result = _module().inventory(text)
    for name in ("distribution-proxy", "buildkit-git-source", "archive-extraction"):
        assert result["surfaces"][name]["named_symbols_present"] is True
    assert result["risk_acceptance"] == "NOT-GRANTED"


@pytest.mark.parametrize("text", ["", "nm: no symbols", "001 T unknown.package.Function\n"])
def test_failed_or_unrecognizable_symbol_inventory_fails_closed(text):
    with pytest.raises(ValueError):
        _module().inventory(text)


def test_invalid_symbol_line_reports_bounded_diagnostic_without_inference():
    with pytest.raises(ValueError, match="line 3") as error:
        _module().inventory(BASE + "invalid-format " + "x" * 1000)
    assert "invalid-format" in str(error.value)
    assert len(str(error.value)) < 300


def test_release_retains_raw_symbol_input_for_parser_failure_review():
    import yaml

    workflow = yaml.safe_load((ROOT / ".github/workflows/backend-release.yml").read_text())
    steps = workflow["jobs"]["release"]["steps"]
    retained = next(step for step in steps if step.get("name") == "Retain client symbol evidence")
    assert "always()" in retained["if"]
    assert "${{ runner.temp }}/launchpad-oc-symbols.txt" in retained["with"]["path"]


def test_actual_go_elf_metadata_symbol_is_valid_not_a_parse_failure():
    # Exact rejected line from run 38638924962, raw nm input line 58340.
    result = _module().inventory(BASE + "       0 _ go.go\n")
    assert result["symbols_count"] == 3
    assert result["risk_acceptance"] == "NOT-GRANTED"
    assert result["staging_qualified"] is False


def test_archive_creation_is_not_mislabeled_as_named_vulnerable_extraction():
    result = _module().inventory(BASE + "003 T github.com/moby/go-archive.TarWithOptions\n")
    assert result["surfaces"]["archive-extraction"]["named_symbols_present"] is True
    assert result["surfaces"]["archive-vulnerable-extraction-call-sites"]["named_symbols_present"] is False
    extracted = _module().inventory(BASE + "003 T github.com/moby/go-archive.UntarUncompressed\n")
    assert extracted["surfaces"]["archive-vulnerable-extraction-call-sites"]["named_symbols_present"] is True
    assert extracted["not_affected_declared"] is False
