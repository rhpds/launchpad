"""The backend must build the confinement fix, not just retain experiment proof."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_backend_builds_fixed_archive_and_compatible_parser_with_regressions():
    recipe = (ROOT / "backend/Containerfile").read_text()
    assert "ARG GO_BUILDKIT_VERSION=v0.31.1" in recipe
    assert "ARG GO_ARCHIVE_VERSION=v0.3.0" in recipe
    assert "git apply --check /opt/launchpad-security-patches/oc-client.patch" in recipe
    assert "git apply /opt/launchpad-security-patches/oc-client.patch" in recipe
    assert "-require=github.com/moby/go-archive@${GO_ARCHIVE_VERSION}" in recipe
    assert "-replace=github.com/moby/go-archive=/tmp/launchpad-go-archive" in recipe
    assert "./pkg/cli/image/archive ./pkg/cli/image/extract" in recipe
    assert "./pkg/helpers/newapp/docker/dockerfile" in recipe
    assert "include_gcs include_oss containers_image_openpgp" in recipe
    assert "go-archive@v0.1.0" not in recipe
    assert "h1:nos4BtzzUIqB406BgQnWGMI4qib9BZ8XUHU+ucv/n1c=" in recipe
    for proof in ("oc-build-info.txt", "oc-source-patch-sha256.txt", "archive-upstream.json"):
        assert f"/opt/launchpad-client-proof/{proof}" in recipe


def test_compatibility_alias_cannot_replace_the_upstream_extractor():
    compatibility = (ROOT / "backend/security-patches/archive_compat.go").read_text()
    assert "type Compression = compression.Compression" in compatibility
    assert '"github.com/moby/go-archive/compression"' in compatibility
    assert "func " not in compatibility
    assert '"os"' not in compatibility


def test_oc_patch_delegates_writes_and_preserves_header_alterations():
    patch = (ROOT / "backend/security-patches/oc-client.patch").read_text()
    assert "+\treturn securearchive.UnpackLayer(dest, reader, opts)" in patch
    assert "+\t\terr := alterLayer(tw, layer, options.AlterHeaders)" in patch
    assert "-func createTarFile(" in patch
    assert "+\t\tif keyValue && position%3 == 2 {" in patch
    assert "ENV EQ== OTHER=two" in patch
