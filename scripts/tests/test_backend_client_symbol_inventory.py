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
