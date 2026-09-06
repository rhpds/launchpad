from pathlib import Path

import pytest
import yaml
from app.adapters.file.catalog import FileCatalogAdapter
from app.domain.enums import CatalogStatus
from app.services.catalog_onboarding import build_catalog_item, load_intake

ROOT = Path(__file__).resolve().parents[2]
INTAKE_PATH = ROOT / "catalog-onboarding/multi-agent-quickstart.yaml"
CATALOG_PATH = ROOT / "catalog/multi-agent-quickstart/catalog-item.yaml"
CONTENT_ROOT = ROOT / "content-multi-agent-quickstart"
TRACKS = {
    "track-1-local": "track-1-local.adoc",
    "track-2-openshift": "track-2-openshift.adoc",
    "track-3-blueprint": "track-3-blueprint.adoc",
}


def test_multi_agent_quickstart_is_imported_as_a_distinct_fail_closed_item():
    intake = load_intake(INTAKE_PATH)
    catalog = yaml.safe_load(CATALOG_PATH.read_text())

    assert catalog == build_catalog_item(intake)
    assert catalog["catalog_item_id"] == "multi-agent-quickstart"
    assert catalog["display_name"] == "Build Multi-Agent AI Systems with Open Protocols"
    assert catalog["version"] == "0.2.4"
    assert catalog["status"] == "draft"
    assert catalog["metadata"]["onboarding_managed"] is True
    assert catalog["metadata"]["activation_blockers"]
    assert catalog["metadata"]["certification_stage"] == (
        "twenty-five-seat-certified"
    )
    assert catalog["metadata"]["max_workshop_seats"] == 25
    assert catalog["metadata"]["certification_proof_contract"] == (
        "certification/catalog/multi-agent-quickstart.yaml"
    )


def test_multi_agent_quickstart_preserves_immutable_source_provenance():
    intake = load_intake(INTAKE_PATH)
    catalog = build_catalog_item(intake)
    metadata = catalog["metadata"]

    assert metadata["source_references"]["original_lab"] == {
        "repo_url": "https://github.com/jkershawrh/multi-agent-quickstart.git",
        "revision": "8a8e0241265e69be81bf28060c4a96be38d5c244",
        "path": ".",
    }
    assert metadata["workload_repo"] == "https://github.com/rhpds/launchpad.git"
    assert metadata["workload_revision"] == (
        "beb5ca39747937dd684a1d2e0ce55fe6165a89dc"
    )
    assert metadata["workload_deploy_path"] == "deploy/workloads/multi-agent-seat"
    assert metadata["workload_source_kind"] == "launchpad-seat-chart"
    assert metadata["workload_gitops_ready"] is True
    assert metadata["workload_identity_value_path"] == "identity"
    assert metadata["workload_runtime_secret_name"] == "multi-agent-runtime"
    assert metadata["workload_runtime_secret_value_path"] == "runtime.existingSecret"
    assert metadata["workload_runtime_secret_sources"] == {
        "MODEL_ENDPOINT": {"source": "maas_endpoint"},
        "MODEL_API_KEY": {"source": "maas_api_key"},
        "MODEL_NAME": {"source": "requested_model"},
        "AGENT_AUTH_TOKEN": {"source": "generated_password", "length": 48},
    }
    assert metadata["workload_helm_values"] == {
        "image": {
            "repository": (
                "image-registry.openshift-image-registry.svc:5000/"
                "partner-ai-launchpad/multi-agent-quickstart"
            ),
            "digest": (
                "sha256:14ea7dfe1b1c018b0dfe473c0c640f3a2ec03015da7a8c5625ac8f224597d67d"
            ),
        }
    }


def test_multi_agent_showroom_is_native_launchpad_content():
    playbook = yaml.safe_load((ROOT / "site-multi-agent-quickstart.yml").read_text())
    component = yaml.safe_load((CONTENT_ROOT / "antora.yml").read_text())
    pages = CONTENT_ROOT / "modules/ROOT/pages"
    guide = "\n".join(path.read_text() for path in sorted(pages.glob("*.adoc")))

    assert playbook["content"]["sources"] == [
        {"url": ".", "start_path": "content-multi-agent-quickstart"}
    ]
    assert "releases/download/patternfly-6/" in playbook["ui"]["bundle"]["url"]
    assert component["asciidoc"]["attributes"]["project_name"] == "%namespace%"
    assert component["asciidoc"]["attributes"]["maas_model"] == "%maas_model%"
    assert "Launchpad has already authenticated this terminal" in guide
    assert "oc login -u" not in guide
    for concept in (
        "A2A",
        "semantic routing",
        "MCP",
        "guardrails",
        "OpenTelemetry",
    ):
        assert concept in guide


def test_multi_agent_is_one_lab_with_all_three_upstream_tracks():
    catalog = yaml.safe_load(CATALOG_PATH.read_text())
    metadata = catalog["metadata"]
    pages = CONTENT_ROOT / "modules/ROOT/pages"
    nav = (CONTENT_ROOT / "modules/ROOT/nav.adoc").read_text()
    index = (pages / "index.adoc").read_text()

    assert metadata["single_environment"] is True
    assert metadata["track_count"] == 3
    assert [track["id"] for track in metadata["learning_tracks"]] == list(TRACKS)
    assert [track["title"] for track in metadata["learning_tracks"]] == [
        "Run locally",
        "Build and operate on OpenShift",
        "Advanced blueprint alignment",
    ]

    for track_id, filename in TRACKS.items():
        assert (pages / filename).is_file()
        assert f"xref:{filename}" in nav
        assert f"xref:{filename}" in index
        assert track_id in (pages / filename).read_text()

    assert "one catalog item" in index
    assert "one participant environment" in index


def test_multi_agent_track_scope_is_explicit_and_does_not_overclaim_track_three():
    pages = CONTENT_ROOT / "modules/ROOT/pages"
    track_1 = (pages / TRACKS["track-1-local"]).read_text()
    track_2 = (pages / TRACKS["track-2-openshift"]).read_text()
    track_3 = (pages / TRACKS["track-3-blueprint"]).read_text()

    assert "Docker Compose" in track_1
    assert "pre-provisioned OpenShift runtime" in track_1
    assert "Track 2: Build and Operate on OpenShift" in track_2
    assert "oc auth can-i" in track_2
    assert "oc create configmap workflow-policy" in track_2
    assert "oc set env deployment/multi-agent -c executor" in track_2
    assert "oc rollout undo deployment/multi-agent" in track_2
    for agent in ("research", "analyst", "executor"):
        assert agent in track_2
    assert "Learner Evidence" in track_2
    assert "Kagenti" in track_3
    assert "OpenTelemetry" in track_3
    assert "not an end-to-end validated deployment" in track_3


def test_multi_agent_quickstart_cannot_activate_with_import_blockers():
    adapter = FileCatalogAdapter(str(ROOT / "catalog"))

    with pytest.raises(ValueError, match="activation blocker"):
        adapter.set_status("multi-agent-quickstart", CatalogStatus.ACTIVE)
