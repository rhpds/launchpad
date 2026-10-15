from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'deploy/launchpad/overlays/flightpath-candidate'
IMAGE = 'ghcr.io/jkershawrh/launchpad-backend-flightpath-candidate@sha256:3bedbc0cef3c09c86e440eff8a883043c9dde9687fd686fe7c9fd1e1a24aabd8'


def test_backend_private_pull_credential_is_only_on_backend_image_consumers():
    rendered = subprocess.run(
        ['oc', 'kustomize', str(OVERLAY)], check=True, text=True, capture_output=True
    ).stdout
    documents = list(yaml.safe_load_all(rendered))
    expected = {'backend', 'lifecycle-worker', 'public-access-gateway',
                'lifecycle-scheduler', 'participant-identity-reconciler'}
    seen = set()
    for document in documents:
        if not document or document.get('kind') not in {'Deployment', 'CronJob'}:
            continue
        spec = document.get('spec', {}).get('template', {}).get('spec', {})
        if document['kind'] == 'CronJob':
            spec = document['spec']['jobTemplate']['spec']['template']['spec']
        name = document['metadata']['name']
        secrets = spec.get('imagePullSecrets', [])
        if name in expected:
            seen.add(name)
            assert {'name': 'launchpad-backend-ghcr-pull'} in secrets
            assert any(c['image'] == IMAGE for c in spec['containers'])
        else:
            assert {'name': 'launchpad-backend-ghcr-pull'} not in secrets
    assert seen == expected


def test_cleanup_verifier_is_enabled_with_a_bounded_wait():
    config = yaml.safe_load((OVERLAY / 'patch-configmap.yaml').read_text())['data']
    assert config['CLEANUP_VERIFY_RESIDUE'] == 'true'
    assert config['CLEANUP_VERIFICATION_TIMEOUT_SECONDS'] == '600'
