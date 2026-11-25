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
    assert "candidate_id=\"$(jq -r '.source.target.imageID // empty' vulnerability-report.json)\"" in gate['run']
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
    assert 'path="${ACCEPTANCE#./}"' in gate['run']
    assert 'cp "$path" staging-risk-acceptance.yaml' in gate['run']
    assert gate['env']['WORKFLOW_SHA'] == '${{ github.workflow_sha }}'
    assert '--acceptance staging-risk-acceptance.yaml --source-revision "$EXPECTED_SHA"' in gate['run']
    evidence = next(step for step in steps if step['name'] == 'Retain pre-publication evidence')
    assert 'staging-risk-acceptance.yaml' in evidence['with']['path']


def test_terminal_release_rejects_a_short_revision_before_checkout():
    """Checkout resolves a non-SHA input as a branch name, so an abbreviated
    SHA fails as 'git fetch refs/heads/<sha>' rather than as bad input."""
    steps = yaml.safe_load(
        (ROOT / '.github/workflows/terminal-release.yml').read_text())['jobs']['release']['steps']
    preflight = steps[0]
    assert preflight['name'] == 'Reject a revision that is not a full commit SHA'
    assert '^[0-9a-f]{40}$' in preflight['run']
    assert preflight['env']['EXPECTED_SHA'] == '${{ inputs.expected_sha }}'
    checkout = next(i for i, step in enumerate(steps)
                    if step.get('uses', '').startswith('actions/checkout@'))
    assert steps.index(preflight) < checkout


def test_signed_acceptance_is_materialised_from_the_workflow_revision():
    """The record must name the revision being released, and a commit cannot
    contain a file that names its own SHA: committing the record changes the
    SHA it names. So the record lives one commit later, on the workflow
    revision, and is materialised from there - while the gate still binds it
    to EXPECTED_SHA and refuses an empty record."""
    steps = yaml.safe_load(
        (ROOT / '.github/workflows/terminal-release.yml').read_text())['jobs']['release']['steps']
    run = next(s for s in steps
               if s['name'] == 'Block unresolved full-inventory security findings')['run']
    assert 'git fetch --depth=1 origin "$WORKFLOW_SHA"' in run
    assert 'git show "$WORKFLOW_SHA:$path" > staging-risk-acceptance.yaml' in run
    assert run.index('git fetch') < run.index('git show')
    assert 'test -s staging-risk-acceptance.yaml' in run
    assert '--source-revision "$EXPECTED_SHA"' in run
    evidence = next(s for s in steps if s['name'] == 'Retain pre-publication evidence')
    assert 'staging-risk-acceptance.yaml' in evidence['with']['path']


def test_published_digest_is_proven_to_be_the_scanned_candidate():
    """A pre-push scan has no repository digest, so the acceptance binds by
    enumeration. The publish step must close that gap by proving the registry
    serves the same config digest the gate verified."""
    steps = yaml.safe_load(
        (ROOT / '.github/workflows/terminal-release.yml').read_text())['jobs']['release']['steps']
    publish = next(step for step in steps
                   if step['name'] == 'Publish immutable candidate and record digest')
    run = publish['run']
    assert 'scanned_config="$(jq -r \'.source.target.imageID\' vulnerability-report.json)"' in run
    assert run.index('scanned_config=') < run.index('docker push')
    assert 'docker buildx imagetools inspect --raw "$digest_ref"' in run
    assert "jq -r '.config.digest // empty'" in run
    assert 'test "$published_config" = "$scanned_config"' in run
    assert '--arg image_id "$published_config"' in run
    assert 'image_id:$image_id' in run
    assert steps.index(publish) < next(
        i for i, step in enumerate(steps)
        if step['name'] == 'Sign the published digest with GitHub OIDC')


def test_no_release_workflow_trusts_the_daemon_image_id():
    """On a containerd-store runner `docker image inspect .Id` is the manifest
    digest, while the scanner reports the config digest. Run 45713500003
    compared the two and rejected a matching candidate as INVALID (exit 2),
    and buildx reports only the manifest digest too, so the pre-push identity
    has to come from the report and be bound at publication."""
    for path in ('.github/workflows/terminal-release.yml',
                 '.github/workflows/backend-release.yml'):
        source = (ROOT / path).read_text()
        assert "$(docker image inspect" not in source, path
        assert "steps.build.outputs.imageid" not in source, path
        assert "source.target.imageID" in source, path
