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

# odo is at its terminal upstream release (v3.16.1) and no fixed artifact
# exists from the vendor or the Red Hat mirror. It must be retained untouched
# rather than stripped to reduce finding counts.
UNREFRESHED_TOOLS = ('odo',)


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
    assert 'rm -f /usr/local/bin/odo' not in source and 'rm -f /usr/bin/odo' not in source


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
    assert 'CGO_ENABLED=0 go build -trimpath' in source
    # Static-build tags from the upstream Makefile (DISABLE_CGO / cross
    # targets); without them the vendored gpgme binding fails to build.
    assert 'containers_image_openpgp' in source
    assert 'exclude_graphdriver_btrfs' in source
    assert 'COPY --from=skopeo-build /out/skopeo /usr/bin/skopeo' in source


def test_cli_refresh_documentes_the_unrefreshable_odo_blocker():
    script = (ROOT / 'workshop-images/showroom-terminal/cli-refresh.sh').read_text()
    for tool in UNREFRESHED_TOOLS:
        assert tool in script, f'{tool} retention must be documented in cli-refresh.sh'


def test_terminal_release_workflow_proves_every_learner_cli_still_runs():
    source = (ROOT / '.github/workflows/terminal-release.yml').read_text()
    for tool in ('skopeo', 'helm', 'kn', 'kubectl', 'oc', 'odo', 'opc', 'roxctl', 'tkn', 'tkn-pac'):
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
