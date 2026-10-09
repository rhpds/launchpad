from pathlib import Path


CONTAINERFILE = Path(__file__).resolve().parents[1] / "Containerfile"


def test_cluster_clients_are_explicitly_versioned() -> None:
    text = CONTAINERFILE.read_text()

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

    assert text.count("curl --fail --silent --show-error --location") == 1
