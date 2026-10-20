"""Client migrations must keep legacy protocols and prove actual source provenance."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_backend_candidate_uses_pinned_split_clients_with_compatibility_tests():
    recipe = (ROOT / 'backend/Containerfile').read_text()
    assert 'ARG GO_DOCKERCLIENT_VERSION=v1.13.2' in recipe
    assert 'ARG GO_DISTRIBUTION_VERSION=v3.1.0' in recipe
    assert 'bash /opt/launchpad-security-patches/prepare_client_modules.sh' in recipe
    assert 'git apply --check --unidiff-zero /opt/launchpad-security-patches/oc-sdk-split.patch' in recipe
    assert 'github.com/openshift/library-go/pkg/image/registryclient' in recipe
    assert 'github.com/distribution/distribution/v3/manifest/schema1' in recipe
    assert 'TestGPGSigningMechanismVerify' in recipe
    assert "grep -Fx 'github.com/docker/docker'" in recipe
    assert '/opt/launchpad-client-proof/client-module-proof' in recipe


def test_sdk_source_patch_preserves_archive_confinement_and_legacy_schema_conversion():
    patch = (ROOT / 'backend/security-patches/oc-sdk-split.patch').read_text()
    assert 'github.com/moby/moby/api/types/registry' in patch
    assert 'github.com/moby/sys/user' in patch
    assert 'distribution.LegacyDescriptor(d)' in patch
    assert 'convertToSchema1' not in patch  # No removal or replacement of the conversion path.
    assert 'Skip' not in patch and 'InsecureSkip' not in patch


def test_compatibility_source_preparer_preserves_patched_server_and_module_identity():
    source = (ROOT / 'backend/security-patches/prepare_client_modules.sh').read_text()
    assert 'set -euo pipefail' in source
    assert 'distribution-upstream.json' in source
    assert 'distribution-legacy-upstream.json' in source
    assert 'h1:u1v788HreKTLGdNY6s7px8Exgrs9mZ9UrCDjSrpCM8g=' in source
    assert '/reference' in source and '/manifest/schema1' in source
    assert 'registry/storage' not in source
    assert 'go list -mod=mod -deps' not in source  # The closure proof runs after source tests.
    assert '|| true' not in source


def test_newapp_unit_fixture_only_supplies_three_missing_fedora_fakes():
    patch = (ROOT / 'backend/security-patches/oc-newapp-unit-fixture.patch').read_text()
    additions = [line for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++')]
    removals = [line for line in patch.splitlines() if line.startswith('-') and not line.startswith('---')]
    assert len(additions) == 3 and not removals
    assert all('Resolvers: cmd.Resolvers{DockerSearcher: fakeDockerSearcher()}' in line for line in additions)
    assert 'PrepareAppConfig' not in patch
