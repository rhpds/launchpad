from types import SimpleNamespace
from unittest.mock import MagicMock

from kubernetes.client.exceptions import ApiException

from app.adapters.openshift.cleanup import OpenShiftCleanupAdapter


def test_inspection_counts_retained_volumes_for_only_the_target_namespace():
    adapter = OpenShiftCleanupAdapter.__new__(OpenShiftCleanupAdapter)
    adapter._core_v1 = MagicMock()
    adapter._rbac_v1 = MagicMock()
    adapter._showroom_gitops = MagicMock()
    adapter._workload_gitops = MagicMock()
    missing = ApiException(status=404)
    adapter._core_v1.read_namespace.side_effect = missing
    adapter._rbac_v1.read_namespaced_role_binding.side_effect = missing
    adapter._rbac_v1.read_cluster_role_binding.side_effect = missing
    adapter._showroom_gitops.custom_objects.get_namespaced_custom_object.side_effect = missing
    adapter._workload_gitops.custom_objects.get_namespaced_custom_object.side_effect = missing
    adapter._core_v1.list_persistent_volume.return_value.items = [
        SimpleNamespace(spec=SimpleNamespace(claim_ref=SimpleNamespace(namespace="seat-a"))),
        SimpleNamespace(spec=SimpleNamespace(claim_ref=SimpleNamespace(namespace="seat-b"))),
        SimpleNamespace(spec=SimpleNamespace(claim_ref=None)),
    ]

    assert adapter.inspect_residue("seat-a")["persistent_volume"] == 1
    adapter._core_v1.patch_persistent_volume.assert_not_called()
    adapter._core_v1.delete_persistent_volume.assert_not_called()


def test_volume_inventory_failure_is_not_reported_as_zero_residue():
    adapter = OpenShiftCleanupAdapter.__new__(OpenShiftCleanupAdapter)
    adapter._core_v1 = MagicMock()
    adapter._rbac_v1 = MagicMock()
    adapter._showroom_gitops = MagicMock()
    adapter._workload_gitops = MagicMock()
    adapter._core_v1.list_persistent_volume.side_effect = ApiException(status=403)
    import pytest

    with pytest.raises(ApiException):
        adapter.inspect_residue("seat-a")
