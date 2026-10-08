"""Read-only preflight for the Flightpath Authentik workforce canary.

The report deliberately contains no token or Secret value. It checks the
public OIDC contract and, when requested, only the shape and decoded strength
of the already-installed Kubernetes Secret.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import urllib.error
import urllib.request
from typing import Any

DEFAULT_ISSUER = "https://auth.smg-helix.ai/application/o/launchpad-workforce/"
DEFAULT_JWKS_URL = f"{DEFAULT_ISSUER}jwks/"
DEFAULT_NAMESPACE = "launchpad-flightpath-candidate"
DEFAULT_SECRET = "launchpad-authentik-workforce"
REQUIRED_SCOPES = {"openid", "profile", "email", "groups"}


def _check(check_id: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": check_id, "passed": bool(passed), "detail": detail}


def evaluate_discovery(
    discovery: dict[str, Any],
    jwks: dict[str, Any],
    *,
    expected_issuer: str = DEFAULT_ISSUER,
    expected_jwks_url: str = DEFAULT_JWKS_URL,
) -> dict[str, Any]:
    """Evaluate public OIDC metadata without accepting permissive fallbacks."""
    scopes = set(discovery.get("scopes_supported") or [])
    response_types = set(discovery.get("response_types_supported") or [])
    pkce_methods = set(discovery.get("code_challenge_methods_supported") or [])
    authorization_endpoint = str(discovery.get("authorization_endpoint") or "")
    token_endpoint = str(discovery.get("token_endpoint") or "")
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    rs256_keys = [
        key
        for key in (keys if isinstance(keys, list) else [])
        if isinstance(key, dict)
        and key.get("kid")
        and key.get("kty") == "RSA"
        and key.get("alg", "RS256") == "RS256"
        and key.get("use", "sig") == "sig"
    ]
    checks = [
        _check(
            "AUTH-PREFLIGHT-ISSUER",
            discovery.get("issuer") == expected_issuer,
            "discovery issuer exactly matches the configured issuer",
        ),
        _check(
            "AUTH-PREFLIGHT-JWKS",
            discovery.get("jwks_uri") == expected_jwks_url,
            "discovery JWKS URI exactly matches the backend verifier",
        ),
        _check(
            "AUTH-PREFLIGHT-AUTHORIZATION-HTTPS",
            authorization_endpoint.startswith("https://"),
            "authorization endpoint uses HTTPS",
        ),
        _check(
            "AUTH-PREFLIGHT-TOKEN-HTTPS",
            token_endpoint.startswith("https://"),
            "token endpoint uses HTTPS",
        ),
        _check(
            "AUTH-PREFLIGHT-CODE-FLOW",
            "code" in response_types,
            "authorization-code response type is advertised",
        ),
        _check(
            "AUTH-PREFLIGHT-PKCE",
            "S256" in pkce_methods,
            "S256 PKCE is advertised",
        ),
        _check(
            "AUTH-PREFLIGHT-SCOPES",
            REQUIRED_SCOPES.issubset(scopes),
            "openid, profile, email, and groups scopes are advertised",
        ),
        _check(
            "AUTH-PREFLIGHT-RS256-KEY",
            bool(rs256_keys),
            "at least one identified RSA signing key is available",
        ),
    ]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def _decoded_length(encoded: Any) -> int | None:
    if not isinstance(encoded, str):
        return None
    try:
        return len(base64.b64decode(encoded, validate=True))
    except (ValueError, TypeError):
        return None


def _decoded_text(encoded: Any) -> str | None:
    if not isinstance(encoded, str):
        return None
    try:
        return base64.b64decode(encoded, validate=True).decode("utf-8")
    except (UnicodeDecodeError, ValueError, TypeError):
        return None


def evaluate_secret(
    secret: dict[str, Any], expected_client_id: str = "launchpad-workforce"
) -> dict[str, Any]:
    """Validate required keys without returning any credential material."""
    data = secret.get("data") if isinstance(secret, dict) else None
    data = data if isinstance(data, dict) else {}
    client_id = _decoded_text(data.get("client-id"))
    client_secret_length = _decoded_length(data.get("client-secret"))
    requester_cookie_length = _decoded_length(data.get("requester-cookie-secret"))
    admin_cookie_length = _decoded_length(data.get("admin-cookie-secret"))
    checks = [
        {
            "key": "client-id",
            "passed": client_id == expected_client_id,
            "requirement": f"exactly {expected_client_id}",
        },
        {
            "key": "client-secret",
            "passed": client_secret_length is not None and client_secret_length >= 32,
            "requirement": "at least 32 decoded bytes",
        },
        {
            "key": "requester-cookie-secret",
            "passed": requester_cookie_length in {16, 24, 32},
            "requirement": "16, 24, or 32 decoded bytes",
        },
        {
            "key": "admin-cookie-secret",
            "passed": admin_cookie_length in {16, 24, 32},
            "requirement": "16, 24, or 32 decoded bytes",
        },
    ]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "launchpad-authentik-preflight/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise TypeError("endpoint did not return a JSON object")
    return value


def _load_cluster_secret(namespace: str, name: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["oc", "-n", namespace, "get", "secret", name, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise TypeError("Secret response was not a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issuer", default=DEFAULT_ISSUER)
    parser.add_argument("--jwks-url", default=DEFAULT_JWKS_URL)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--check-cluster-secret", action="store_true")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    parser.add_argument("--secret-name", default=DEFAULT_SECRET)
    args = parser.parse_args()

    discovery_url = f"{args.issuer}.well-known/openid-configuration"
    report: dict[str, Any] = {
        "schema_version": "launchpad.redhat.com/authentik-canary-preflight/v1",
        "mutates_cluster": False,
        "issuer": args.issuer,
        "discovery": {"passed": False, "checks": []},
        "secret": {"checked": False, "passed": None, "checks": []},
    }
    try:
        discovery = _get_json(discovery_url, args.timeout)
        jwks = _get_json(args.jwks_url, args.timeout)
        report["discovery"] = evaluate_discovery(
            discovery,
            jwks,
            expected_issuer=args.issuer,
            expected_jwks_url=args.jwks_url,
        )
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        report["discovery"]["failure"] = type(exc).__name__

    if args.check_cluster_secret:
        report["secret"]["checked"] = True
        try:
            report["secret"] = {
                "checked": True,
                **evaluate_secret(_load_cluster_secret(args.namespace, args.secret_name)),
            }
        except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
            report["secret"]["failure"] = type(exc).__name__

    report["passed"] = report["discovery"]["passed"] and (
        not args.check_cluster_secret or report["secret"]["passed"] is True
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
