import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from preflight_authentik_canary import evaluate_discovery, evaluate_secret  # noqa: I001


ISSUER = "https://auth.smg-helix.ai/application/o/launchpad-workforce/"


def test_discovery_must_match_exact_issuer_and_jwks_and_advertise_code_flow():
    report = evaluate_discovery(
        {
            "issuer": ISSUER,
            "jwks_uri": f"{ISSUER}jwks/",
            "authorization_endpoint": "https://auth.smg-helix.ai/application/o/authorize/",
            "token_endpoint": "https://auth.smg-helix.ai/application/o/token/",
            "response_types_supported": ["code"],
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": ["openid", "profile", "email", "groups"],
        },
        {
            "keys": [
                {"kid": "key-1", "kty": "RSA", "alg": "RS256", "use": "sig"}
            ]
        },
        expected_issuer=ISSUER,
        expected_jwks_url=f"{ISSUER}jwks/",
    )

    assert report["passed"] is True
    assert all(check["passed"] for check in report["checks"])


def test_discovery_fails_closed_on_wrong_issuer_missing_pkce_or_signing_key():
    report = evaluate_discovery(
        {
            "issuer": "https://wrong.example/",
            "jwks_uri": f"{ISSUER}jwks/",
            "authorization_endpoint": "http://auth.example/authorize",
            "token_endpoint": "https://auth.smg-helix.ai/application/o/token/",
            "response_types_supported": ["token"],
            "code_challenge_methods_supported": ["plain"],
            "scopes_supported": ["openid"],
        },
        {"keys": []},
        expected_issuer=ISSUER,
        expected_jwks_url=f"{ISSUER}jwks/",
    )

    assert report["passed"] is False
    assert {item["id"] for item in report["checks"] if not item["passed"]} == {
        "AUTH-PREFLIGHT-ISSUER",
        "AUTH-PREFLIGHT-AUTHORIZATION-HTTPS",
        "AUTH-PREFLIGHT-CODE-FLOW",
        "AUTH-PREFLIGHT-PKCE",
        "AUTH-PREFLIGHT-SCOPES",
        "AUTH-PREFLIGHT-RS256-KEY",
    }


def test_secret_check_reports_only_presence_and_strength_not_values():
    secret = {
        "data": {
            "client-id": base64.b64encode(b"launchpad-workforce").decode(),
            "client-secret": base64.b64encode(b"x" * 32).decode(),
            "requester-cookie-secret": base64.b64encode(b"r" * 32).decode(),
            "admin-cookie-secret": base64.b64encode(b"a" * 32).decode(),
        }
    }

    report = evaluate_secret(secret)

    assert report["passed"] is True
    assert "data" not in report
    assert "x" * 32 not in str(report)


def test_secret_check_rejects_missing_or_weak_material_without_echoing_it():
    report = evaluate_secret(
        {
            "data": {
                "client-id": base64.b64encode(b"launchpad-workforce").decode(),
                "client-secret": base64.b64encode(b"short").decode(),
            }
        }
    )

    assert report["passed"] is False
    failures = {item["key"] for item in report["checks"] if not item["passed"]}
    assert failures == {
        "client-secret",
        "requester-cookie-secret",
        "admin-cookie-secret",
    }


def test_secret_check_rejects_client_id_that_cannot_match_backend_audience():
    secret = {
        "data": {
            "client-id": base64.b64encode(b"another-client").decode(),
            "client-secret": base64.b64encode(b"x" * 32).decode(),
            "requester-cookie-secret": base64.b64encode(b"r" * 32).decode(),
            "admin-cookie-secret": base64.b64encode(b"a" * 32).decode(),
        }
    }

    report = evaluate_secret(secret)

    assert report["passed"] is False
    assert report["checks"][0] == {
        "key": "client-id",
        "passed": False,
        "requirement": "exactly launchpad-workforce",
    }
