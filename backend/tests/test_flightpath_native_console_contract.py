"""Counterfactual local proof of existing native Console callback translation.

These tests do not change the deployed Console hostname or tunnel settings.
"""

import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
NATIVE = "console-openshift-console.apps.flightpath.fm2aihpcsed.com"
PUBLIC = "labs.smg-helix.ai"


@pytest.fixture
def router(monkeypatch):
    configuration = {
        "OPENSHIFT_CONSOLE_HOST": NATIVE,
        "OPENSHIFT_CONSOLE_UPSTREAM_HOST": NATIVE,
        "OPENSHIFT_CONSOLE_CALLBACK_URL": f"https://{NATIVE}/auth/callback",
        "OPENSHIFT_OAUTH_HOST": "oauth-openshift.apps.flightpath.fm2aihpcsed.com",
        "KEYCLOAK_PUBLIC_HOST": PUBLIC,
        "OPENSHIFT_INGRESS_DOMAIN": "apps.flightpath.fm2aihpcsed.com",
    }
    for key, value in configuration.items():
        monkeypatch.setenv(key, value)
    spec = importlib.util.spec_from_file_location(
        "flightpath_native_console", ROOT / "deploy/tunnel-oncluster/router.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_participant_authorization_can_use_native_operator_callback(router):
    query = [
        ("client_id", "console"),
        ("redirect_uri", f"https://{PUBLIC}/auth/callback"),
        ("state", "participant-state"),
    ]
    forwarded = dict(router._rewrite_oauth_request_query(router.OAUTH_ORIGIN, query, PUBLIC))
    assert forwarded["redirect_uri"] == f"https://{NATIVE}/auth/callback"
    assert forwarded["idp"] == "launchpad-public"
    assert forwarded["state"] == "participant-state"


def test_console_bootstrap_and_namespace_path_remain_on_participant_origin(router):
    native = f"https://{NATIVE}/k8s/ns/seat-example/core~v1~Pod"
    assert router._rewrite_url(native, PUBLIC) == f"https://{PUBLIC}/k8s/ns/seat-example/core~v1~Pod"
    body = f'{{"consoleURL":"https://{NATIVE}","basePath":"/"}}'.encode()
    assert router._rewrite_console_body(body, PUBLIC) == (
        f'{{"consoleURL":"https://{PUBLIC}","basePath":"/"}}'.encode()
    )


def test_native_console_redirect_stays_public_for_participant_browser(router):
    callback = quote(f"https://{NATIVE}/auth/callback", safe="")
    url = (
        "https://oauth-openshift.apps.flightpath.fm2aihpcsed.com/oauth/authorize"
        f"?client_id=console&redirect_uri={callback}"
    )
    rewritten = router._rewrite_url(url, PUBLIC)
    assert urlsplit(rewritten).netloc == PUBLIC
    assert parse_qs(urlsplit(rewritten).query)["redirect_uri"] == [
        f"https://{PUBLIC}/auth/callback"
    ]


def test_labs_root_and_namespace_console_remain_separate_dispatches(router):
    assert router._select_upstream("")[0] == router.GATEWAY_ORIGIN
    assert router._select_upstream("labs/example/showroom/")[0] == router.GATEWAY_ORIGIN
    assert router._select_upstream("k8s/ns/seat-example/core~v1~Pod")[0] == router.CONSOLE_ORIGIN


def test_checked_in_flightpath_tunnel_uses_native_operator_console_callback():
    resources = yaml.safe_load_all((ROOT / "deploy/tunnel-oncluster/flightpath-deployment.yaml").read_text())
    deployment = next(resource for resource in resources if resource.get("kind") == "Deployment")
    router = next(container for container in deployment["spec"]["template"]["spec"]["containers"] if container["name"] == "router")
    env = {entry["name"]: entry.get("value") for entry in router["env"]}
    assert env["OPENSHIFT_CONSOLE_UPSTREAM_HOST"] == NATIVE
    assert env["OPENSHIFT_CONSOLE_CALLBACK_URL"] == f"https://{NATIVE}/auth/callback"
    assert env["KEYCLOAK_PUBLIC_HOST"] == PUBLIC


def test_native_route_patch_does_not_replace_unrelated_console_settings():
    patch = json.loads((ROOT / "deploy/console-embed/flightpath-native-route.patch.json").read_text())
    assert patch == {"spec": {"route": None}}
