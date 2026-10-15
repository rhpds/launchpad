"""A green probe must not omit release identity for advanced VM labs."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_probe_checks_do_not_rely_on_old_bash_errexit_for_double_brackets():
    source = (ROOT / "scripts/certify-virtualization-ai-seat.sh").read_text()
    bare_checks = [line.strip() for line in source.splitlines()
                   if line.strip().startswith("[[") and line.strip().endswith("]]")]
    assert bare_checks == [], bare_checks


@pytest.mark.parametrize("catalog_id", ["virtualization-ai-401", "virtualization-ai-501"])
def test_advanced_vm_probe_binds_the_current_source_and_immutable_images(catalog_id):
    metadata = yaml.safe_load((ROOT / "catalog" / catalog_id / "catalog-item.yaml").read_text())["metadata"]
    source = (ROOT / "scripts/certify-virtualization-ai-seat.sh").read_text()
    branch = source.split(f"  {catalog_id})", 1)[1].split(";;", 1)[0]
    assert f'source_revision="{metadata["workload_revision"]}"' in branch
    values = metadata["workload_helm_values"]
    if catalog_id == "virtualization-ai-401":
        images = [values[key]["image"] for key in ("presentation", "operationsAdapter")]
        expected = [f'{image["repository"]}@{image["digest"]}' for image in images]
    else:
        expected = [values["presentation_image"], values["workload_image"]]
    for image in expected:
        assert image in branch
    contract = yaml.safe_load((ROOT / "certification/catalog" / f"{catalog_id}.yaml").read_text())
    assertions = contract["spec"]["seat_probe"]["json_assertions"]
    assert {"path": "provenance.source_revision", "equals": metadata["workload_revision"]} in assertions
    for path, image in zip(("runtime_images.presentation", "runtime_images.adapter"), expected):
        assert {"path": path, "equals": image} in assertions
    runtime = source.split("stage=runtime-images", 1)[1].split("stage=presentation", 1)[0]
    assert '[[ "$presentation_image" == "$expected_presentation_image" ]]' in runtime
    assert '[[ "$adapter_image" == "$expected_adapter_image" ]]' in runtime
    assert 'get deployments' in runtime
    assert 'if [[ "$catalog_id"' not in runtime


@pytest.mark.parametrize("failure", [None, "missing-image", "missing-source"])
def test_runtime_identity_stage_checks_deployment_data_without_cluster_access(tmp_path, failure):
    source = (ROOT / "scripts/certify-virtualization-ai-seat.sh").read_text()
    runtime = source.split("stage=runtime-images", 1)[1].split("stage=presentation", 1)[0]
    presentation = "ghcr.io/example/presentation@sha256:" + "a" * 64
    adapter = "ghcr.io/example/adapter@sha256:" + "b" * 64
    deployments = {"items": [{"spec": {"template": {"spec": {"containers": [
        {"image": presentation}, {"image": adapter if failure != "missing-image" else "unexpected:latest"},
    ]}}}}]}
    fake_oc = tmp_path / "oc"
    fake_oc.write_text(
        f"#!{sys.executable}\nimport os,sys\n"
        "assert sys.argv[3:] == ['get','deployments','-n','test-seat','-o','json']\n"
        "sys.stdout.write(os.environ['FAKE_DEPLOYMENTS'])\n"
    )
    fake_oc.chmod(0o700)
    environment = {
        **os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
        "FAKE_DEPLOYMENTS": json.dumps(deployments),
        "KUBECONFIG": str(tmp_path / "no-cluster-config"),
        "work_dir": str(tmp_path), "namespace": "test-seat",
        "source_revision": "" if failure == "missing-source" else "a" * 40,
        "expected_presentation_image": presentation, "expected_adapter_image": adapter,
    }
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", runtime],
        env=environment, capture_output=True, text=True, timeout=10,
    )
    assert (result.returncode == 0) is (failure is None), result.stderr
