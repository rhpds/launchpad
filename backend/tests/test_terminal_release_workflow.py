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
                     'Inventory fixable high and critical vulnerabilities',
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
    assert "docker image inspect --format '{{.Id}}'" in gate['run']
    assert '--expected-image "$candidate" --expected-image-id "$candidate_id"' in gate['run']
    assert 'continue-on-error' not in gate
    assert '|| true' not in gate['run']
    runtime = next(step for step in steps if step['name'] == 'Verify isolated persistent shell runtime')
    assert runtime['id'] == 'runtime_smoke'
    evidence = next(step for step in steps if step['name'] == 'Retain pre-publication evidence')
    assert 'always()' in evidence['if']
    assert 'staging-security-decision.json' in evidence['with']['path']
    assert steps.index(gate) < next(i for i, step in enumerate(steps)
                                  if step['name'] == 'Log in to GHCR')


def test_terminal_release_acceptance_input_defaults_to_a_clean_scan():
    workflow = yaml.safe_load(
        (ROOT / '.github/workflows/terminal-release.yml').read_text())
    dispatch = workflow[True]['workflow_dispatch']['inputs']
    assert dispatch['acceptance']['default'] == ''
    assert dispatch['acceptance']['required'] is False


def test_terminal_release_has_one_authoritative_gate_that_honours_a_signed_acceptance():
    steps = yaml.safe_load(
        (ROOT / '.github/workflows/terminal-release.yml').read_text())['jobs']['release']['steps']
    fixable = next(step for step in steps
                   if step['name'] == 'Inventory fixable high and critical vulnerabilities')
    assert fixable['with']['fail-build'] is False
    gate = next(step for step in steps
                if step['name'] == 'Block unresolved full-inventory security findings')
    assert gate['env']['ACCEPTANCE'] == '${{ inputs.acceptance }}'
    assert gate['env']['EXPECTED_SHA'] == '${{ inputs.expected_sha }}'
    assert 'test -f "$ACCEPTANCE"' in gate['run']
    assert 'cp "$ACCEPTANCE" staging-risk-acceptance.yaml' in gate['run']
    assert '--acceptance "$ACCEPTANCE" --source-revision "$EXPECTED_SHA"' in gate['run']
    evidence = next(step for step in steps if step['name'] == 'Retain pre-publication evidence')
    assert 'staging-risk-acceptance.yaml' in evidence['with']['path']
