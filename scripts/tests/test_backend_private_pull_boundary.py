from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'deploy/launchpad/overlays/flightpath-candidate'
IMAGE = 'ghcr.io/jkershawrh/launchpad-backend-flightpath-candidate@sha256:3bedbc0cef3c09c86e440eff8a883043c9dde9687fd686fe7c9fd1e1a24aabd8'


def test_backend_private_pull_credential_is_only_on_backend_and_workers():
    documents = list(yaml.safe_load_all((OVERLAY / 'patch-runtime.yaml').read_text()))
    for document in documents:
        spec = document.get('spec', {}).get('template', {}).get('spec', {})
        name = document['metadata']['name']
        secrets = spec.get('imagePullSecrets', [])
        if name in {'backend', 'lifecycle-worker'}:
            assert secrets == [{'name': 'launchpad-backend-ghcr-pull'}, {'name': 'launchpad-registry-pull'}]
            container = next(c for c in spec['containers'] if c['name'] == name)
            assert container['image'] == IMAGE
        else:
            assert {'name': 'launchpad-backend-ghcr-pull'} not in secrets


def test_cleanup_verifier_is_enabled_with_a_bounded_wait():
    config = yaml.safe_load((OVERLAY / 'patch-configmap.yaml').read_text())['data']
    assert config['CLEANUP_VERIFY_RESIDUE'] == 'true'
    assert config['CLEANUP_VERIFICATION_TIMEOUT_SECONDS'] == '600'
