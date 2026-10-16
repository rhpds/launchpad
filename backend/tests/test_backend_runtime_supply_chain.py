from pathlib import Path


CONTAINERFILE = Path(__file__).resolve().parents[1] / "Containerfile"


def test_cluster_clients_are_explicitly_versioned() -> None:
    text = CONTAINERFILE.read_text()

    assert "FROM registry.access.redhat.com/ubi9/go-toolset:1.26 AS oc-builder" in text
    assert "ARG OPENSHIFT_CLIENT_COMMIT=" in text
    assert "ARG GO_X_TEXT_VERSION=v0.41.0" in text
    assert "ARG HELM_VERSION=" in text
    assert "/ocp/stable/" not in text
    assert "helm-v3.17.3" not in text
    assert "openshift-client-linux.tar.gz" not in text
    assert "git checkout --detach \"${OPENSHIFT_CLIENT_COMMIT}\"" in text
    assert "golang.org/x/text=golang.org/x/text@${GO_X_TEXT_VERSION}" in text
    assert "include_gcs include_oss containers_image_openpgp" in text
    assert "COPY --from=oc-builder /tmp/oc-bin /usr/local/bin/oc" in text
    assert "${HELM_VERSION}" in text


def test_runtime_removes_unused_node_toolchain_and_updates_packaging_metadata() -> None:
    text = CONTAINERFILE.read_text()

    assert "dnf -y remove npm 'nodejs*'" in text
    assert "pip install --no-cache-dir --upgrade setuptools" in text


def test_downloads_fail_closed() -> None:
    text = CONTAINERFILE.read_text()

    assert "https://get.helm.sh/" not in text
    assert 'git checkout --detach "${HELM_SOURCE_COMMIT}"' in text


def test_cluster_clients_use_patched_toolchain_and_network_module() -> None:
    text = CONTAINERFILE.read_text()
    assert "ENV GOTOOLCHAIN=go1.26.9" in text
    assert "ARG GO_X_NET_VERSION=v0.60.0" in text
    assert "golang.org/x/net=golang.org/x/net@${GO_X_NET_VERSION}" in text
    assert "COPY --from=oc-builder /tmp/helm-bin /usr/local/bin/helm" in text


def test_oc_builder_documents_the_unconsumable_distribution_fix() -> None:
    text = CONTAINERFILE.read_text()
    # GHSA-f2g3-hh2r-cwgc and GHSA-3p65-76g6-3w7r are fixed only in
    # distribution v3.1.0, which removed the registry/client packages that
    # openshift/library-go imports. A pinned replace to v3.1.0 breaks the
    # oc build (verified in run 38916954262), and oc master still pins the
    # same 2023 pseudo-version. The constraint must stay documented in the
    # Containerfile instead of carrying a broken replace.
    assert "distribution/v3 stays at the inherited 2023 pseudo-version on purpose" in text
    assert "GHSA-f2g3-hh2r-cwgc and GHSA-3p65-76g6-3w7r are fixed only in v3.1.0" in text
    assert "registry-server code paths" in text
    assert "GO_DISTRIBUTION_VERSION" not in text
