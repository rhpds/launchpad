"""Negative regressions for staging access and cleanup boundaries."""

from unittest.mock import MagicMock

import pytest
from app.adapters.openshift.cleanup import OpenShiftCleanupAdapter
from app.auth import oauth
from app.domain.enums import SessionStatus
from app.domain.models import LabSession
from app.services.provisioning import LifecycleOwnershipLostError, ProvisioningService
from kubernetes.client.rest import ApiException
from starlette.requests import Request


def test_residue_checks_exact_namespace_image_puller_name(monkeypatch):
    monkeypatch.setenv("OPERATOR_NAMESPACE", "control-plane")
    adapter = OpenShiftCleanupAdapter.__new__(OpenShiftCleanupAdapter)
    adapter._core_v1 = MagicMock()
    adapter._rbac_v1 = MagicMock()
    adapter._showroom_gitops = MagicMock()
    adapter._workload_gitops = MagicMock()
    missing = ApiException(status=404)
    adapter._core_v1.list_persistent_volume.return_value.items = []
    adapter._core_v1.read_namespace.side_effect = missing
    adapter._rbac_v1.read_cluster_role_binding.side_effect = missing

    def read_binding(name, namespace):
        if (name, namespace) == ("seat-a-image-puller", "control-plane"):
            return MagicMock()
        raise missing

    adapter._rbac_v1.read_namespaced_role_binding.side_effect = read_binding
    result = adapter.inspect_residue("seat-a")
    assert result["image_puller_role_binding"] == 1
    adapter._rbac_v1.read_namespaced_role_binding.assert_called_once_with(
        "seat-a-image-puller", "control-plane"
    )


def _force_service(cleanup):
    service = ProvisioningService.__new__(ProvisioningService)
    session = LabSession(
        session_id="test-session", request_id="test-order",
        tenant_id="test-tenant", catalog_item_id="test-catalog",
        namespace="seat-a", cluster_ref="flightpath", status=SessionStatus.CLEANUP_FAILED,
    )
    service._sessions = {session.session_id: session}
    service.maas_key_broker = None
    service._get_cleanup = MagicMock(return_value=cleanup)
    service._scrub_credentials = lambda value: value
    service._save_session = lambda value: service._sessions.update({value.session_id: value})
    service.pool = MagicMock()
    return service


@pytest.mark.parametrize("require_success", [False, True])
@pytest.mark.parametrize("residue", ["persistent_volume", "image_puller_role_binding"])
def test_force_reclaim_cannot_bypass_enabled_residue_gate(monkeypatch, require_success, residue):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    monkeypatch.setenv("CLEANUP_VERIFICATION_TIMEOUT_SECONDS", "0")
    cleanup = MagicMock()
    cleanup.inspect_residue.return_value = {
        "namespace": 0, "showroom_application": 0, "workload_application": 0,
        "image_puller_role_binding": 0, "persistent_volume": 0,
    }
    cleanup.inspect_residue.return_value[residue] = 1
    service = _force_service(cleanup)
    result = service.force_reclaim_session("test-session", require_cleanup_success=require_success)
    assert result.status == SessionStatus.CLEANUP_FAILED
    assert residue in result.lifecycle_events[-1].reason
    service.pool.release.assert_not_called()


def test_workshop_fallback_does_not_turn_residue_failure_into_success(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    monkeypatch.setenv("CLEANUP_VERIFICATION_TIMEOUT_SECONDS", "0")
    cleanup = MagicMock()
    cleanup.inspect_residue.return_value = {
        "namespace": 0, "showroom_application": 0, "workload_application": 0,
        "image_puller_role_binding": 0, "persistent_volume": 1,
    }
    service = _force_service(cleanup)
    service.reclaim_session = MagicMock(return_value=service._sessions["test-session"])
    assert "persistent_volume" in service._reclaim_workshop_session("test-session")
    assert service._sessions["test-session"].status == SessionStatus.CLEANUP_FAILED


@pytest.mark.parametrize("cleanup", [None, MagicMock()])
def test_force_reclaim_requires_valid_inventory_when_enabled(monkeypatch, cleanup):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    monkeypatch.setenv("CLEANUP_VERIFICATION_TIMEOUT_SECONDS", "0")
    if cleanup is not None:
        cleanup.inspect_residue.side_effect = RuntimeError("inventory unavailable")
    service = _force_service(cleanup)
    assert service.force_reclaim_session("test-session").status == SessionStatus.CLEANUP_FAILED
    service.pool.release.assert_not_called()


def test_force_reclaim_accepts_verified_zero_residue(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    cleanup = MagicMock()
    cleanup.inspect_residue.return_value = {
        "namespace": 0, "showroom_application": 0, "workload_application": 0,
        "image_puller_role_binding": 0, "persistent_volume": 0,
    }
    service = _force_service(cleanup)
    assert service.force_reclaim_session("test-session").status == SessionStatus.RECLAIMED
    service.pool.release.assert_called_once_with("test-order")


def test_force_reclaim_preserves_legacy_behavior_when_gate_disabled(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "false")
    cleanup = MagicMock()
    service = _force_service(cleanup)
    assert service.force_reclaim_session("test-session").status == SessionStatus.RECLAIMED
    cleanup.inspect_residue.assert_not_called()


def test_force_reclaim_does_not_swallow_lost_ownership(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    cleanup = MagicMock()
    cleanup.inspect_residue.side_effect = LifecycleOwnershipLostError("lease lost")
    service = _force_service(cleanup)
    with pytest.raises(LifecycleOwnershipLostError):
        service.force_reclaim_session("test-session")
    service.pool.release.assert_not_called()


def test_force_reclaim_denies_delete_failure_even_without_require_success(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    cleanup = MagicMock()
    cleanup.cleanup.side_effect = RuntimeError("delete forbidden")
    service = _force_service(cleanup)
    assert service.force_reclaim_session("test-session").status == SessionStatus.CLEANUP_FAILED
    service.pool.release.assert_not_called()


def test_normal_reclaim_denies_missing_adapter_when_gate_enabled(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    monkeypatch.setenv("CLEANUP_VERIFICATION_TIMEOUT_SECONDS", "0")
    service = _force_service(None)
    assert service.reclaim_session("test-session").status == SessionStatus.CLEANUP_FAILED
    service.pool.release.assert_not_called()


@pytest.mark.parametrize("groups", [[], ["launchpad-requesters"], ["system:cluster-admins"]])
def test_oidc_cannot_inherit_legacy_admin_or_tenant_by_username(monkeypatch, groups):
    monkeypatch.setattr(oauth, "AUTH_ENABLED", True)
    monkeypatch.setattr(oauth, "OIDC_JWT_HOSTS", {"requester-auth.example.com"})
    monkeypatch.setattr(oauth, "ADMIN_USERS", {"kubeadmin"})
    monkeypatch.setenv("TENANT_USER_MAP", '{"kubeadmin":["legacy-tenant"]}')
    monkeypatch.setattr(oauth, "verify_oidc_token", lambda _: {
        "sub": "independent-oidc-subject", "preferred_username": "kubeadmin", "groups": groups,
    })
    request = Request({
        "type": "http", "method": "GET", "path": "/",
        "headers": [(b"host", b"requester-auth.example.com"),
                    (b"authorization", b"Bearer test-signed-token")],
    })
    user = oauth.get_current_user(request)
    assert not user.is_admin
    assert user.tenant_ids == []
