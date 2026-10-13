from unittest.mock import Mock

import pytest

from app.services.provisioning import ProvisioningService


def test_enabled_completion_gate_refuses_retained_storage(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    monkeypatch.setenv("CLEANUP_VERIFICATION_TIMEOUT_SECONDS", "0")
    cleanup = Mock()
    cleanup.inspect_residue.return_value = {
        "namespace": 0, "showroom_application": 0, "workload_application": 0,
        "image_puller_role_binding": 0, "persistent_volume": 1,
    }
    svc = ProvisioningService.__new__(ProvisioningService)
    with pytest.raises(ValueError, match="persistent_volume"):
        svc._verify_cleanup_completion(cleanup, "seat-a", None)


def test_enabled_completion_gate_requires_complete_inventory(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    cleanup = Mock()
    cleanup.inspect_residue.return_value = {"namespace": 0}
    svc = ProvisioningService.__new__(ProvisioningService)
    with pytest.raises(ValueError, match="incomplete"):
        svc._verify_cleanup_completion(cleanup, "seat-a", None)


def test_enabled_completion_gate_accepts_complete_zero_residue(monkeypatch):
    monkeypatch.setenv("CLEANUP_VERIFY_RESIDUE", "true")
    cleanup = Mock()
    cleanup.inspect_residue.return_value = {
        "namespace": 0, "showroom_application": 0, "workload_application": 0,
        "image_puller_role_binding": 0, "persistent_volume": 0,
    }
    svc = ProvisioningService.__new__(ProvisioningService)
    svc._verify_cleanup_completion(cleanup, "seat-a", None)
    cleanup.cleanup.assert_not_called()
