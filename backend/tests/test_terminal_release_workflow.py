from pathlib import Path

import yaml

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


def test_terminal_release_blocks_unresolved_inventory_before_publication():
    source = (ROOT / '.github/workflows/terminal-release.yml').read_text()
    steps = yaml.safe_load(source)['jobs']['release']['steps']
    gate = next(step for step in steps
                if step['name'] == 'Block unresolved full-inventory security findings')
    assert '!cancelled()' in gate['if']
    assert "steps.runtime_smoke.outcome == 'success'" in gate['if']
    assert 'check_backend_staging_security.py vulnerability-report.json' in gate['run']
    assert '--component terminal' in gate['run']
    assert 'continue-on-error' not in gate
    assert '|| true' not in gate['run']
    runtime = next(step for step in steps if step['name'] == 'Verify isolated persistent shell runtime')
    assert runtime['id'] == 'runtime_smoke'
    evidence = next(step for step in steps if step['name'] == 'Retain pre-publication evidence')
    assert 'always()' in evidence['if']
    assert 'staging-security-decision.json' in evidence['with']['path']
    assert steps.index(gate) < next(i for i, step in enumerate(steps)
                                  if step['name'] == 'Log in to GHCR')
