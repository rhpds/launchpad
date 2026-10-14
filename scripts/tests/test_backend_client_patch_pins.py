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


def test_git_and_billy_fixes_stay_on_supported_v5_major():
    text = (ROOT / "backend/Containerfile").read_text()
    assert "ARG GO_GIT_VERSION=v5.19.2" in text
    assert "ARG GO_BILLY_VERSION=v5.9.0" in text
    assert "-replace=github.com/go-git/go-git/v5=github.com/go-git/go-git/v5@${GO_GIT_VERSION}" in text
    assert "-replace=github.com/go-git/go-billy/v5=github.com/go-git/go-billy/v5@${GO_BILLY_VERSION}" in text
    assert 'grep -F "${GO_GIT_VERSION}"' in text
    assert 'grep -F "${GO_BILLY_VERSION}"' in text
    assert "github.com/go-git/go-git/v6" not in text


def test_telemetry_and_fulcio_pins_are_verified_and_same_major():
    text = (ROOT / "backend/Containerfile").read_text()
    assert "ARG OTEL_VERSION=v1.41.0" in text
    assert "ARG FULCIO_VERSION=v1.8.6" in text
    assert "-replace=go.opentelemetry.io/otel=go.opentelemetry.io/otel@${OTEL_VERSION}" in text
    assert "-replace=go.opentelemetry.io/otel/trace=go.opentelemetry.io/otel/trace@${OTEL_VERSION}" in text
    assert "-replace=github.com/sigstore/fulcio=github.com/sigstore/fulcio@${FULCIO_VERSION}" in text
    assert 'grep -F "${OTEL_VERSION}"' in text
    assert 'grep -F "${FULCIO_VERSION}"' in text
