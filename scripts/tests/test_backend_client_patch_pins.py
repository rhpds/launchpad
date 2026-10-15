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


def test_archive_upgrade_requires_the_reviewed_compatibility_and_confinement_fix():
    text = (ROOT / "backend/Containerfile").read_text()
    # The original bare v0.3 override did not compile against Docker 28.
    # Permit it only with the tested compatibility copy, confined extraction
    # patch, exact upstream checksum and build-time behavioral regressions.
    assert "ARG GO_ARCHIVE_VERSION=v0.3.0" in text
    assert "-require=github.com/moby/go-archive@${GO_ARCHIVE_VERSION}" in text
    assert "-replace=github.com/moby/go-archive=/tmp/launchpad-go-archive" in text
    assert "h1:nos4BtzzUIqB406BgQnWGMI4qib9BZ8XUHU+ucv/n1c=" in text
    assert "archive_compat.go /tmp/launchpad-go-archive/launchpad_compat.go" in text
    assert "git apply --check /opt/launchpad-security-patches/oc-client.patch" in text
    assert "./pkg/cli/image/archive ./pkg/cli/image/extract" in text
    assert "./pkg/helpers/newapp/docker/dockerfile" in text
    assert "OPENSHIFT_CLIENT_COMMIT=d0f23b14fbf35493e5b713e25ecf662ec239e76c" in text


def test_compression_fix_is_verified_when_linked_not_required_in_helm():
    text = (ROOT / "backend/Containerfile").read_text()
    assert "ARG GO_COMPRESS_VERSION=v1.18.7" in text
    pin = "-replace=github.com/klauspost/compress=github.com/klauspost/compress@${GO_COMPRESS_VERSION}"
    assert text.count(pin) == 2
    assert text.count('grep -F "${GO_COMPRESS_VERSION}"') == 2
    # The prior scan locates this dependency in oc only. Helm may omit it;
    # retain its metadata and reject an old version if it becomes linked.
    assert 'go version -m /tmp/helm-bin > /tmp/helm-build-info.txt' in text
    assert 'if grep -F "github.com/klauspost/compress" /tmp/helm-build-info.txt; then' in text
    assert 'cat /tmp/helm-build-info.txt' in text
