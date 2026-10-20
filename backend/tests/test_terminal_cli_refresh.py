import re

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Pinned vendor artifacts for the embedded learner CLIs. Each entry is the
# tool, the exact upstream release, and the SHA256 that the build must verify
# before the binary replaces the inherited base-image copy. Checksums for
# helm, tkn, tkn-pac and opc match the vendor-published checksum files.
PINNED_CLI_TOOLS = {
    'helm': 'v3.22.1',
    'oc': '4.22.18',
    'kubectl': '4.22.18',
    'kn': 'v1.23.0',
    'tkn': 'v0.46.1',
    'tkn-pac': 'v0.52.0',
    'opc': 'v1.24.0',
    'roxctl': '4.11.5',
    # skopeo publishes no release binaries; it is built from the immutable
    # v1.24.1 source tag in the Containerfile with a pinned Go toolchain.
    'skopeo': 'v1.24.1',
}

# odo was removed with owner authorization on 2026-10-16: upstream ended at
# v3.16.1 with no fixed artifact, no lab content references it, and it carried
# 21 Critical + 106 High fixable findings. The removal, rationale and restore
# path must stay documented in cli-refresh.sh.
REMOVED_TOOLS = ('odo',)


def test_cli_refresh_script_pins_every_tool_with_immutable_checksums():
    script = ROOT / 'workshop-images/showroom-terminal/cli-refresh.sh'
    assert script.exists(), 'cli-refresh.sh must exist beside the Containerfile'
    source = script.read_text()
    assert 'set -euo pipefail' in source
    for tool, version in PINNED_CLI_TOOLS.items():
        assert version in source, f'{tool} {version} must be pinned'
    pinned_shas = re.findall(r'\b[0-9a-f]{64}\b', source)
    # skopeo is built from source in the Containerfile; odo is retained.
    assert len(pinned_shas) >= len(PINNED_CLI_TOOLS) - 2, (
        'every downloaded artifact must carry a pinned SHA256'
    )
    assert 'sha256sum --check' in source
    assert '|| true' not in source


def test_cli_refresh_documents_the_authorized_odo_removal():
    script = (ROOT / 'workshop-images/showroom-terminal/cli-refresh.sh').read_text()
    for tool in REMOVED_TOOLS:
        assert f'rm -f /usr/local/bin/{tool}' in script, (
            f'{tool} removal must be explicit in cli-refresh.sh'
        )
        assert 'owner authorization' in script, (
            'the removal must record the authorization basis'
        )
        assert 'restore path' in script.lower() or 'Restore path' in script, (
            'the removal must document how to restore the tool'
        )
        assert 'v3.16.1' in script, 'the terminal upstream version must be recorded'
        assert f'{tool} version' not in (
            ROOT / '.github/workflows/terminal-release.yml'
        ).read_text(), f'{tool} is removed and must not be asserted in the runtime check'


def test_containerfile_runs_cli_refresh_after_os_refresh_before_entrypoint():
    source = (ROOT / 'workshop-images/showroom-terminal/Containerfile').read_text()
    assert 'COPY cli-refresh.sh /tmp/cli-refresh.sh' in source
    assert 'bash /tmp/cli-refresh.sh' in source
    assert (
        source.index('dnf -y --refresh upgrade')
        < source.index('bash /tmp/cli-refresh.sh')
        < source.index('USER 1001')
    )


def test_containerfile_builds_skopeo_from_immutable_source():
    source = (ROOT / 'workshop-images/showroom-terminal/Containerfile').read_text()
    # Pinned Go toolchain image digest for the builder stage.
    assert (
        'FROM golang:1.27.2@sha256:820153096fda4de6ac1b7194d12e416b7dd8f4e9a33d17e0345b111b945162d8 AS skopeo-build'
        in source
    )
    # Checksum-pinned immutable upstream source tarball.
    assert (
        'ADD --checksum=sha256:6a3f342a327ec7684198eb0e15114940b6101506db48d9a96590f5942cb3b335'
        in source
    )
    assert 'refs/tags/v1.24.1.tar.gz' in source
    assert 'CGO_ENABLED=0 go build -mod=mod -trimpath' in source
    # Static-build tags from the upstream Makefile (DISABLE_CGO / cross
    # targets); without them the vendored gpgme binding fails to build.
    assert 'containers_image_openpgp' in source
    assert 'exclude_graphdriver_btrfs' in source
    assert 'COPY --from=skopeo-build /out/skopeo /usr/bin/skopeo' in source


def test_cli_refresh_removes_staging_artifacts_before_layer_close():
    # Run 38916694544 proved the scanner picks up leftover /tmp copies of the
    # installed binaries, double-counting findings and shipping duplicate
    # binaries in the image. Every downloaded or extracted artifact must be
    # removed in the same layer that installs the tools.
    source = (ROOT / 'workshop-images/showroom-terminal/cli-refresh.sh').read_text()
    assert 'rm -f /tmp/helm-v3.22.1-linux-amd64.tar.gz' in source
    assert 'rm -rf /tmp/linux-amd64' in source
    for leftover in (
        '/tmp/kn-linux-amd64',
        '/tmp/roxctl-4.11.5',
        '/tmp/oc',
        '/tmp/kubectl',
        '/tmp/tkn',
        '/tmp/tkn-pac',
        '/tmp/opc',
    ):
        assert leftover in source, f'{leftover} must be removed after install'


def test_terminal_release_workflow_proves_every_learner_cli_still_runs():
    source = (ROOT / '.github/workflows/terminal-release.yml').read_text()
    for tool in ('skopeo', 'helm', 'kn', 'kubectl', 'oc', 'opc', 'roxctl', 'tkn', 'tkn-pac'):
        assert f'command -v "$tool"' in source or f'command -v {tool}' in source, (
            f'{tool} must remain present and executable in the runtime check'
        )
        assert f'{tool} --version' in source or f'{tool} version' in source, (
            f'{tool} command compatibility must be proven after the refresh'
        )


def test_cli_refresh_uses_official_vendor_sources_only():
    source = (ROOT / 'workshop-images/showroom-terminal/cli-refresh.sh').read_text()
    allowed_hosts = (
        'https://get.helm.sh/',
        'https://mirror.openshift.com/',
        'https://github.com/knative/client/',
        'https://github.com/tektoncd/cli/',
        'https://github.com/openshift-pipelines/pipelines-as-code/',
        'https://github.com/openshift-pipelines/opc/',
    )
    urls = [
        line.strip().rstrip('\\').strip().strip('"')
        for line in source.splitlines()
        if 'https://' in line and 'curl' not in line
    ]
    for url in urls:
        assert url.startswith(allowed_hosts), f'unexpected artifact source: {url}'


def test_skopeo_source_build_pins_and_tests_fixed_dependencies():
    source = (ROOT / 'workshop-images/showroom-terminal/Containerfile').read_text()
    for module, version in (
        ('golang.org/x/net', 'v0.60.0'),
        ('golang.org/x/text', 'v0.41.0'),
        ('golang.org/x/crypto', 'v0.57.0'),
        ('google.golang.org/grpc', 'v1.83.1'),
    ):
        assert f'-replace={module}={module}@{version}' in source
        assert f'grep -F "{module}"' in source
        assert f'grep -F "{version}"' in source
    assert 'go test -mod=mod' in source
    assert 'go build -mod=mod -trimpath' in source
    assert 'skopeo-build-info.txt' in source
    assert 'COPY --from=skopeo-build /out/skopeo-build-info.txt' in source
