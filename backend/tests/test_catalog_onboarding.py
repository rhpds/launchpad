from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from app.adapters.file.catalog import FileCatalogAdapter
from app.domain.enums import CatalogStatus
from app.services.catalog_onboarding import (
    build_catalog_item,
    load_intake,
    validate_intake,
)

ROOT = Path(__file__).resolve().parents[2]
INTAKE_PATH = ROOT / "catalog-onboarding/agentops-observability.yaml"
CATALOG_PATH = ROOT / "catalog/agentops-observability/catalog-item.yaml"


def test_agentops_is_registered_as_a_fail_closed_draft():
    intake = load_intake(INTAKE_PATH)
    catalog = yaml.safe_load(CATALOG_PATH.read_text())

    assert catalog == build_catalog_item(intake)
    assert catalog["catalog_item_id"] == "agentops-observability"
    assert catalog["status"] == "draft"
    assert catalog["metadata"]["certification_stage"] == "implementation"
    assert catalog["metadata"]["max_workshop_seats"] == 1
    assert catalog["metadata"]["activation_blockers"]
    assert catalog["metadata"]["showroom_content_repo_url"] == (
        "https://github.com/rhpds/launchpad.git"
    )
    assert catalog["metadata"]["showroom_content_ref"] == (
        "0d697f3ddd1e5008dfd9bb32c3e3bdd0398383a9"
    )
    assert catalog["metadata"]["showroom_content_playbook"] == ("site-agentops-observability.yml")
    assert catalog["metadata"]["showroom_content_start_path"] == ("content-agentops-observability")
    assert catalog["metadata"]["workload_repo"] == "https://github.com/rhpds/launchpad.git"
    assert catalog["metadata"]["workload_revision"] == ("2fcf40b74387046b657e0050513144afead09892")
    assert catalog["metadata"]["workload_deploy_path"] == "deploy/workloads/agentops-seat"
    assert catalog["metadata"]["workload_deployment_scope"] == "seat"
    assert catalog["metadata"]["workload_source_kind"] == "launchpad-seat-chart"
    assert catalog["metadata"]["workload_gitops_ready"] is False
    assert catalog["metadata"]["workload_identity_value_path"] == "identity"
    assert catalog["metadata"]["workload_runtime_secret_name"] == "agentops-runtime"
    assert catalog["metadata"]["source_references"]["automation"]["revision"] == (
        "6ea100531ac869fa66abe69ae223d6b56dbce9a2"
    )
    assert catalog["metadata"]["source_references"]["upstream_showroom"]["revision"] == (
        "f1881c61de55ebf5640c27e76469f4efe458edaf"
    )
    assert catalog["metadata"]["source_references"]["agnosticv"]["path"] == (
        "agd_v2/agentops-intel"
    )


def test_agentops_cannot_be_activated_while_intake_blockers_remain():
    adapter = FileCatalogAdapter(str(ROOT / "catalog"))

    with pytest.raises(ValueError, match="activation blocker"):
        adapter.set_status("agentops-observability", CatalogStatus.ACTIVE)


def test_agentops_intake_captures_the_large_lab_runtime_contract():
    intake = load_intake(INTAKE_PATH)
    runtime = intake["runtime"]
    certification = intake["certification"]

    assert runtime["deployment_type"] == "helm"
    assert runtime["seat_resources"] == {
        "cpu_millicores": 1250,
        "memory_mib": 3072,
        "pods": 11,
        "storage_gib": 25,
    }
    assert set(runtime["required_capabilities"]) >= {
        "openshift",
        "showroom",
        "model_endpoint",
        "agentops_observability_stack",
        "rhoai",
        "mlflow",
        "user_workload_monitoring",
        "openshift_logging",
        "data_science_pipelines",
    }
    assert runtime["required_models"] == ["granite-3.2-8b-tools"]
    assert [tab["id"] for tab in runtime["tabs"]] == [
        "openshift-console",
        "terminal",
        "mlflow",
        "mortgage-ai",
        "grafana",
        "rhoai",
        "mlflow-docs",
        "rhoai-docs",
    ]
    assert runtime["deployment_scope"] == "seat"
    assert runtime["workload"]["source_kind"] == "launchpad-seat-chart"
    assert runtime["workload"]["identity_value_path"] == "identity"
    assert runtime["workload"]["runtime_secret_value_path"] == "runtime.existingSecret"
    assert certification["promotion_sequence"] == [1, 5, 25]
    blockers = "\n".join(certification["activation_blockers"])
    assert "mutable latest UI bundle" not in blockers
    assert "instead of its original qwen3-14b" not in blockers


def test_validator_accepts_complete_local_source_contract(tmp_path: Path):
    showroom = tmp_path / "showroom"
    content = showroom / "content"
    pages = content / "modules/ROOT/pages"
    pages.mkdir(parents=True)
    (showroom / "site.yml").write_text(
        "content:\n  sources:\n    - url: .\n      start_path: content\n"
    )
    (content / "antora.yml").write_text(
        "name: modules\ntitle: Example\nversion: ~\nnav:\n  - modules/ROOT/nav.adoc\n"
    )
    (content / "modules/ROOT/nav.adoc").write_text("* xref:index.adoc[Start]\n")
    (pages / "index.adoc").write_text("= Start\nimage::diagram.svg[]\n")
    images = content / "modules/ROOT/images"
    images.mkdir(parents=True)
    (images / "diagram.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>\n")

    workload = tmp_path / "workload"
    chart = workload / "deploy/helm/example"
    chart.mkdir(parents=True)
    (chart / "Chart.yaml").write_text("apiVersion: v2\nname: example\nversion: 1.0.0\n")
    (chart / "values.yaml").write_text("replicaCount: 1\n")

    intake = {
        "api_version": "launchpad.redhat.com/v1alpha1",
        "catalog": {
            "catalog_item_id": "example",
            "display_name": "Example",
            "description": "Example catalog intake",
            "category": "guided_build",
            "version": "0.1.0",
        },
        "sources": {
            "showroom": {
                "repo_url": "https://github.com/example/showroom.git",
                "revision": "a" * 40,
                "playbook": "site.yml",
                "start_path": "content",
            },
            "workload": {
                "repo_url": "https://github.com/example/workload.git",
                "revision": "b" * 40,
                "deploy_path": "deploy/helm/example",
            },
        },
        "runtime": {
            "deployment_type": "helm",
            "required_capabilities": ["openshift", "showroom"],
            "required_models": [],
            "seat_resources": {
                "cpu_millicores": 100,
                "memory_mib": 256,
                "pods": 1,
                "storage_gib": 0,
            },
            "tabs": [{"id": "terminal", "title": "Terminal"}],
        },
        "certification": {
            "stage": "intake",
            "max_workshop_seats": 1,
            "promotion_sequence": [1, 5, 25],
            "activation_blockers": ["One-seat live certification is incomplete."],
        },
    }

    report = validate_intake(
        intake,
        showroom_dir=showroom,
        workload_dir=workload,
        catalog=build_catalog_item(intake),
    )

    assert report["validation_status"] == "pass"
    assert report["activation_status"] == "blocked"
    assert report["errors"] == []
    assert report["checks"]["showroom_structure"] == "pass"
    assert report["checks"]["workload_structure"] == "pass"
    assert report["checks"]["catalog_drift"] == "pass"


def test_validator_rejects_mutable_refs_and_missing_showroom_assets(tmp_path: Path):
    showroom = tmp_path / "showroom"
    pages = showroom / "content/modules/ROOT/pages"
    pages.mkdir(parents=True)
    (showroom / "site.yml").write_text(
        "content:\n  sources:\n    - url: .\n      start_path: content\n"
    )
    (showroom / "content/antora.yml").write_text(
        "name: modules\ntitle: Example\nversion: ~\nnav:\n  - modules/ROOT/nav.adoc\n"
    )
    (showroom / "content/modules/ROOT/nav.adoc").write_text("* xref:index.adoc[Start]\n")
    (pages / "index.adoc").write_text("= Start\nimage::missing.png[]\n")

    workload = tmp_path / "workload/deploy/helm/example"
    workload.mkdir(parents=True)
    (workload / "Chart.yaml").write_text("apiVersion: v2\nname: example\nversion: 1\n")
    (workload / "values.yaml").write_text("{}\n")

    intake = load_intake(INTAKE_PATH)
    intake["sources"]["showroom"]["revision"] = "main"
    intake["sources"]["showroom"]["start_path"] = "content"
    intake["sources"]["showroom"]["playbook"] = "site.yml"
    intake["sources"]["workload"]["deploy_path"] = "deploy/helm/example"

    report = validate_intake(
        intake,
        showroom_dir=showroom,
        workload_dir=tmp_path / "workload",
    )

    assert report["validation_status"] == "fail"
    assert any("immutable 40-character Git SHA" in error for error in report["errors"])
    assert any("missing.png" in error for error in report["errors"])


def test_validator_rejects_mutable_reference_and_literal_runtime_secret():
    intake = load_intake(INTAKE_PATH)
    intake["references"]["automation"]["revision"] = "main"
    intake["runtime"]["workload"]["runtime_secret_sources"]["LLM_API_KEY"] = {
        "value": "embedded-secret"
    }

    report = validate_intake(intake)

    assert report["validation_status"] == "fail"
    assert any("references.automation.revision" in error for error in report["errors"])
    assert any("Sensitive runtime field 'LLM_API_KEY'" in error for error in report["errors"])


def test_validator_rejects_incomplete_runtime_secret_and_identity_contract():
    intake = load_intake(INTAKE_PATH)
    workload = intake["runtime"]["workload"]
    workload["identity_value_path"] = "bad..path"
    workload["runtime_secret_value_path"] = ""

    report = validate_intake(intake)

    assert report["validation_status"] == "fail"
    assert any("identity_value_path" in error for error in report["errors"])
    assert any("runtime Secret name and value path" in error for error in report["errors"])
