import pytest
from pydantic import ValidationError

from app.domain.enums import CatalogCategory, LabRequestStatus, Persistence
from app.domain.models import LabRequest


def test_verified_internal_request_uses_authenticated_openshift_identity():
    from app.api.routers.lab_requests import _bind_authenticated_requester
    from app.auth.oauth import User

    request = LabRequest(
        tenant_id="tenant-a",
        requester_id="typed-but-untrusted",
        catalog_item_id="guided-rag-on-xeon",
        requested_mode="guided_build",
    )

    bound = _bind_authenticated_requester(
        request,
        User(
            username="lp-stable-participant",
            email="participant@example.com",
            identity_verified=True,
        ),
    )

    assert bound.requester_id == "lp-stable-participant"
    assert bound.metadata["authenticated_requester"] == "lp-stable-participant"


def test_api_key_request_preserves_legacy_requester_identity():
    from app.api.routers.lab_requests import _bind_authenticated_requester
    from app.auth.oauth import User

    request = LabRequest(
        tenant_id="tenant-a",
        requester_id="automation-service",
        catalog_item_id="guided-rag-on-xeon",
        requested_mode="guided_build",
    )

    bound = _bind_authenticated_requester(
        request,
        User(username="api-user", identity_verified=False),
    )

    assert bound.requester_id == "automation-service"
    assert "authenticated_requester" not in bound.metadata


def test_lab_request_accepts_ephemeral(ephemeral_lab_request):
    assert ephemeral_lab_request.persistence == Persistence.EPHEMERAL
    assert ephemeral_lab_request.status == LabRequestStatus.SUBMITTED
    assert ephemeral_lab_request.tenant_id == "partner-oem-a"
    assert ephemeral_lab_request.catalog_item_id == "inference-overdrive-quickstart"
    assert ephemeral_lab_request.request_id  # auto-generated UUID


def test_lab_request_accepts_persistent(persistent_lab_request):
    assert persistent_lab_request.persistence == Persistence.PERSISTENT
    assert persistent_lab_request.status == LabRequestStatus.SUBMITTED
    assert persistent_lab_request.tenant_id == "redhat-internal"
    assert persistent_lab_request.catalog_item_id == "build-a-rag-app"


def test_lab_request_rejects_empty_tenant_id():
    with pytest.raises(ValidationError):
        LabRequest(
            tenant_id="",
            requester_id="user-1",
            catalog_item_id="some-item",
            requested_mode=CatalogCategory.QUICK_START,
        )


def test_lab_request_rejects_empty_catalog_item_id():
    with pytest.raises(ValidationError):
        LabRequest(
            tenant_id="tenant-1",
            requester_id="user-1",
            catalog_item_id="  ",
            requested_mode=CatalogCategory.QUICK_START,
        )


def test_lab_request_auto_generates_request_id():
    req = LabRequest(
        tenant_id="t1",
        requester_id="u1",
        catalog_item_id="c1",
        requested_mode=CatalogCategory.QUICK_START,
    )
    assert len(req.request_id) == 36  # UUID format
