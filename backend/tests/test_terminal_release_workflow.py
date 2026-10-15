from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_terminal_release_is_manual_exact_revision_and_has_no_deployment():
    source = (ROOT / '.github/workflows/terminal-release.yml').read_text()
    assert 'workflow_dispatch:' in source
    assert 'ref: ${{ inputs.expected_sha }}' in source
    assert 'test "$(git rev-parse HEAD)" = "${{ inputs.expected_sha }}"' in source
    assert 'context: workshop-images/showroom-terminal' in source
    assert 'platforms: linux/amd64' in source
    assert 'oc apply' not in source and 'kubectl apply' not in source


def test_terminal_release_checks_persistent_shell_and_supply_chain():
    source = (ROOT / '.github/workflows/terminal-release.yml').read_text()
    for required in ('tmux', 'capture-pane', 'LAUNCHPAD_RECONNECT_OK',
                     'Block fixable high and critical vulnerabilities',
                     'cosign sign', 'cosign verify', 'sbom.spdx.json',
                     'cosign attest', 'cosign verify-attestation',
                     'source_revision', 'workflow_revision'):
        assert required in source
    assert 'actions/attest-build-provenance@' not in source
