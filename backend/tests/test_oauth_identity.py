import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.auth import oauth
from app.api.routers.auth_identity import current_identity


def _request(headers: list[tuple[bytes, bytes]], host: bytes = b"launchpad.apps.example.com") -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"host", host), *headers],
    })


def test_kube_admin_is_admin_without_forwarded_groups(monkeypatch):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "TRUSTED_OAUTH_HOSTS", {"launchpad.apps.example.com"})
    user = oauth.get_current_user(_request([(b"x-forwarded-user", b"kube:admin")]))
    assert user.username == "kube:admin"
    assert user.is_admin is True


def test_regular_oauth_user_is_not_admin_without_forwarded_groups(monkeypatch):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "TRUSTED_OAUTH_HOSTS", {"launchpad.apps.example.com"})
    user = oauth.get_current_user(_request([(b"x-forwarded-user", b"partner-user")]))
    assert user.username == "partner-user"
    assert user.is_admin is False
    assert user.identity_verified is True


def test_oauth_user_gets_tenants_from_identity_map(monkeypatch):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "TRUSTED_OAUTH_HOSTS", {"launchpad.apps.example.com"})
    monkeypatch.setenv("TENANT_USER_MAP", '{"partner-user":["partner-a"]}')

    user = oauth.get_current_user(_request([(b"x-forwarded-user", b"partner-user")]))

    assert user.tenant_ids == ["partner-a"]


def test_oauth_user_gets_tenants_from_group_claims(monkeypatch):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "TRUSTED_OAUTH_HOSTS", {"launchpad.apps.example.com"})

    user = oauth.get_current_user(_request([
        (b"x-forwarded-user", b"partner-user"),
        (b"x-forwarded-groups", b"developers,launchpad-tenant:partner-b"),
    ]))

    assert user.tenant_ids == ["partner-b"]


def test_forwarded_identity_is_rejected_on_public_api_hostname(monkeypatch):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "TRUSTED_OAUTH_HOSTS", {"launchpad.apps.example.com"})
    request = _request(
        [(b"x-forwarded-user", b"kube:admin")],
        host=b"launchpad-api.apps.example.com",
    )
    with pytest.raises(HTTPException) as exc_info:
        oauth.get_current_user(request)
    assert exc_info.value.status_code == 401


def test_current_identity_contract_does_not_expose_groups_or_tenants():
    identity = current_identity(
        oauth.User(
            username="lp-participant",
            email="participant@example.com",
            groups=["private-group"],
            tenant_ids=["tenant-a"],
            is_admin=False,
            identity_verified=True,
        )
    )

    assert identity.model_dump() == {
        "username": "lp-participant",
        "email": "participant@example.com",
        "is_admin": False,
        "identity_verified": True,
    }
