"""Patch only the reviewed client dependencies, preserving the release source."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_client_retains_exact_release_source_with_reviewed_patch_pins():
    text = (ROOT / "backend/Containerfile").read_text()
    assert "OPENSHIFT_CLIENT_COMMIT=d0f23b14fbf35493e5b713e25ecf662ec239e76c" in text
    assert "ARG GO_JOSE_VERSION=v4.1.4" in text
    assert "ARG SPDYSTREAM_VERSION=v0.5.1" in text
    assert "-replace=github.com/go-jose/go-jose/v4=github.com/go-jose/go-jose/v4@${GO_JOSE_VERSION}" in text
    assert "-replace=github.com/moby/spdystream=github.com/moby/spdystream@${SPDYSTREAM_VERSION}" in text


def test_compiled_client_dependency_versions_are_verified():
    text = (ROOT / "backend/Containerfile").read_text()
    assert 'grep -F "github.com/go-jose/go-jose/v4"' in text
    assert 'grep -F "${GO_JOSE_VERSION}"' in text
    assert 'grep -F "github.com/moby/spdystream"' in text
    assert 'grep -F "${SPDYSTREAM_VERSION}"' in text
