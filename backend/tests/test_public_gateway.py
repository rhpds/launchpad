from pathlib import Path

from fastapi.testclient import TestClient

from app.public_gateway import _lab_cards, _username, app


def test_gateway_exposes_only_public_health_identity():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "public-access-gateway"}


def test_gateway_has_no_openapi_or_admin_surface():
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/docs").status_code == 404
    assert client.get("/admin").status_code == 404


def test_participant_home_renders_resume_links_without_exposing_secrets():
    body = _lab_cards([{
        "catalog_slug": "operator-workshop",
        "public_url": "https://operator-123.labs.example.io",
        "expires_at": "2026-09-02T18:00:00Z",
    }])
    assert "operator-workshop" in body
    assert "Resume lab" in body
    assert "https://operator-123.labs.example.io" in body
    assert "code" not in body.casefold()


def test_gateway_exposes_participant_home_and_add_lab_routes():
    paths = {route.path for route in app.routes}
    assert "/my-labs" in paths
    assert "/add-lab" in paths
    assert "/instructions/{path:path}" in paths
    assert "/www/{path:path}" in paths
    assert "/ui-config.yml" in paths
    assert "/terminal/{path:path}" in paths
    assert "/assets/{path:path}" in paths
    assert "/token" in paths
    assert "/ws" in paths


def test_participant_shell_uses_launchpad_navigation_and_switch_identity():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    from app.public_gateway import _page
    body = _page("<h1>My labs</h1>").body.decode()
    assert "AI Launchpad" in body
    assert "My Lab Access" in body
    assert "Log out of lab" in body
    assert "/oauth2/sign_out" in body
    assert "/brand/redhat.png" in body
    assert "/brand/intel.png" in body


def test_gateway_prefers_stable_oidc_username_claim():
    request = type("Request", (), {"headers": {
        "x-forwarded-user": "40982c65-d541-4fca-a92c-44d38885cd45",
        "x-forwarded-email": "lp-87bd01a6f6c73d54ece70b489ceb3957",
    }})()
    assert _username(request) == "lp-87bd01a6f6c73d54ece70b489ceb3957"


def test_gateway_accepts_oauth_proxy_websocket_identity_headers():
    request = type("Request", (), {"headers": {
        "x-auth-request-user": "40982c65-d541-4fca-a92c-44d38885cd45",
        "x-auth-request-email": "lp-87bd01a6f6c73d54ece70b489ceb3957",
    }})()
    assert _username(request) == "lp-87bd01a6f6c73d54ece70b489ceb3957"


def test_oauth_proxy_accepts_unverified_participant_identity_labels():
    manifest = (
        Path(__file__).resolve().parents[2]
        / "deploy/launchpad/base/public-access-gateway.yaml"
    ).read_text()
    assert "--insecure-oidc-allow-unverified-email=true" in manifest
    assert "--oidc-email-claim=preferred_username" in manifest
    assert 'name: PUBLIC_UPSTREAM_TLS_VERIFY, value: "true"' in manifest
