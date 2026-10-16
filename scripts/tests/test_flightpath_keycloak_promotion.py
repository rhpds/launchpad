"""Source contracts for the Flightpath Keycloak isolated upgrade test and promotion helper.

The historical promotion helper patched the obsolete Keycloak CR in the
``keycloak`` namespace and verified artifacts against the retired rhpds
repository. These contracts pin the replacement behavior: an isolated
upgrade proof against a restored copy of the live schema is mandatory
before any live Deployment promotion, and every artifact check targets the
current private repository's registry-backed provenance.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPGRADE_TEST = ROOT / "scripts/test-flightpath-keycloak-upgrade.sh"
PROMOTION = ROOT / "scripts/promote-flightpath-keycloak.sh"


def test_isolated_upgrade_test_fails_closed_on_usage_and_cluster():
    source = UPGRADE_TEST.read_text()
    assert 'set -euo pipefail' in source
    assert 'usage: $0' in source
    assert 'https://api.flightpath.fm2aihpcsed.com:6443' in source
    assert '|| true' not in source


def test_isolated_upgrade_test_verifies_release_supply_chain():
    source = UPGRADE_TEST.read_text()
    assert 'launchpad.redhat.com/keycloak-release/v1' in source
    assert 'ghcr.io/jkershawrh/launchpad-keycloak@sha256' in source.replace('\\', '').replace(
        '${image}', ''
    ) or 'launchpad-keycloak@sha256' in source
    assert 'cosign verify' in source
    assert 'cosign verify-attestation' in source
    assert 'jkershawrh/intel-ai-launchpad' in source
    # GitHub native attestation is unavailable for this private repository.
    assert 'gh attestation' not in source


def test_isolated_upgrade_test_never_touches_the_live_identity_service():
    source = UPGRADE_TEST.read_text()
    assert 'launchpad-keycloak-upgrade-test' in source
    # The live namespace is referenced only for the read-only dump source.
    assert 'pg_dump' in source
    # The candidate must point at the isolated postgres, never the live one:
    # the test namespace resources are created before the Deployment and the
    # dump is restored into the isolated database.
    assert 'launchpad_stage' in source
    assert 'set image deploy/keycloak' not in source
    assert 'patch keycloak keycloak' not in source
    assert 'patch deploy' not in source


def test_isolated_upgrade_test_proves_migration_data_theme_and_residue():
    source = UPGRADE_TEST.read_text()
    assert 'user_entity' in source, 'data integrity must compare user counts'
    assert 'keycloak.realm' in source, 'realm inventory must be verified'
    assert '#191919' in source, 'the dark login card fix must be proven in the rendered page'
    assert 'launchpad.redhat.com/keycloak-isolated-upgrade/v1' in source
    assert 'result' in source and 'passed' in source
    assert 'delete namespace' in source, 'the isolated namespace must be torn down'
    assert 'ignore-not-found' in source or '--wait=true' in source


def test_promotion_requires_isolated_proof_and_targets_the_stage_deployment():
    source = PROMOTION.read_text()
    assert 'set -euo pipefail' in source
    assert 'usage: $0' in source
    assert 'https://api.flightpath.fm2aihpcsed.com:6443' in source
    assert '|| true' not in source
    # The isolated upgrade receipt is a mandatory third input.
    assert 'keycloak-isolated-upgrade/v1' in source
    # The promoted image must match the isolated proof exactly.
    assert 'does not match the isolated upgrade proof' in source
    # Target is the launchpad-stage Deployment, not the obsolete Keycloak CR.
    assert 'launchpad-stage' in source
    assert 'set image deploy/keycloak' in source
    assert 'patch keycloak keycloak' not in source
    assert 'get keycloak keycloak' not in source


def test_promotion_verifies_current_supply_chain_and_login_surface():
    source = PROMOTION.read_text()
    assert 'launchpad.redhat.com/keycloak-release/v1' in source
    assert 'cosign verify' in source
    assert 'cosign verify-attestation' in source
    assert 'jkershawrh/intel-ai-launchpad' in source
    assert 'gh attestation' not in source
    # Post-promotion login checks: the dark card fix and the public surface.
    assert '#191919' in source
    assert 'What you can do in Launchpad' in source
    assert 'Access your lab' in source
