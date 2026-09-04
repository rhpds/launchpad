"""Contract for the repository-owned Antora/Nookbag Showroom package."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


INTEL_GUIDED_LABS = [
    {
        "catalog_id": "intel-xeon6-agent-201",
        "display_name": "Intel Xeon 6 201: Building an AI Agent",
        "playbook": "site-intel-xeon6-agent-201.yml",
        "content_path": "content-intel-xeon6-agent-201",
        "title": "Intel Xeon 6 201 — Building an AI Agent",
        "model": "granite-2b-cpu",
    },
    {
        "catalog_id": "intel-llm-cpu-serving",
        "display_name": "Intel AI Quickstart: Serve LLMs on Intel Xeon CPUs",
        "playbook": "site-intel-llm-cpu-serving.yml",
        "content_path": "content-intel-llm-cpu-serving",
        "title": "Serve LLMs on Intel Xeon CPUs",
        "model": "granite-2b-cpu",
    },
    {
        "catalog_id": "intel-llm-tool-calling",
        "display_name": "Intel AI Quickstart: LLM Tool Calling on Intel",
        "playbook": "site-intel-llm-tool-calling.yml",
        "content_path": "content-intel-llm-tool-calling",
        "title": "Enable AI Tool Calling on OpenShift",
        "model": "granite-2b-cpu",
    },
]


def test_antora_playbook_builds_content_from_this_repository():
    playbook = yaml.safe_load((ROOT / "site.yml").read_text())
    source = playbook["content"]["sources"][0]
    assert source["url"] == "."
    assert source["start_path"] == "content"
    assert "rhdp_showroom_theme" in playbook["ui"]["bundle"]["url"]


def test_operator_workshop_playbook_starts_on_operator_journey():
    playbook = yaml.safe_load((ROOT / "site-openshift-operators.yml").read_text())

    assert playbook["site"]["start_page"] == "modules::index.adoc"
    assert playbook["content"]["sources"][0]["start_path"] == "content-operators"
    assert playbook["asciidoc"]["attributes"]["showroom_journey"] == (
        "openshift-operators"
    )
    assert playbook["output"]["dir"] == "./www"

    operator_index = ROOT / "content-operators/modules/ROOT/pages/index.adoc"
    assert "OpenShift AI Operator Workshop" in operator_index.read_text()
    assert "Inference Overdrive" not in operator_index.read_text()
    assert "*OpenShift Console* operator tab" in operator_index.read_text()
    assert "*launchpad-public*" in operator_index.read_text()
    assert "no separate OpenShift username" in operator_index.read_text()
    assert "{cluster_display_name}" in operator_index.read_text()
    assert "Oberon" not in operator_index.read_text()

    discovery = ROOT / "content-operators/modules/ROOT/pages/02-operator-discovery.adoc"
    assert "{cluster_display_name}" in discovery.read_text()
    assert "Oberon" not in discovery.read_text()

    exercise = ROOT / "content-operators/modules/ROOT/pages/03-deploy-and-observe.adoc"
    exercise_text = exercise.read_text()
    assert "quay.io/openshifttest/hello-openshift:1.2.0" in exercise_text
    assert "curl" in exercise_text


def test_nookbag_config_has_guided_workspace_tabs():
    config = yaml.safe_load((ROOT / "ui-config.yml").read_text())
    assert config["type"] == "showroom"
    assert config["view_switcher"]["default_mode"] == "split"
    names = [tab["name"] for tab in config["tabs"]]
    assert names == ["RAG Workspace", "Terminal", "OpenShift Console"]


def test_guided_rag_journey_is_versioned_as_asciidoc():
    page = ROOT / "content/modules/ROOT/pages/01-guided-rag-welcome.adoc"
    assert page.exists()
    assert "Guided RAG" in page.read_text()
    nav = (ROOT / "content/modules/ROOT/nav.adoc").read_text()
    assert "showroom_journey" in nav
    assert "01-guided-rag-welcome.adoc" in nav


@pytest.mark.parametrize("lab", INTEL_GUIDED_LABS)
def test_intel_guided_lab_is_native_launchpad_content(lab):
    catalog = yaml.safe_load(
        (ROOT / "catalog" / lab["catalog_id"] / "catalog-item.yaml").read_text()
    )
    assert catalog["catalog_item_id"] == lab["catalog_id"]
    assert catalog["display_name"] == lab["display_name"]
    assert catalog["category"] == "guided_build"
    assert catalog["status"] == "active"
    assert set(catalog["required_capabilities"]) >= {
        "openshift",
        "showroom",
        "model_endpoint",
    }
    assert catalog["provisioner_refs"] == ["openshift-provisioner", "showroom"]
    assert catalog["validation_refs"] == [
        "pod-ready",
        "route-accessible",
        "inference-health",
    ]

    metadata = catalog["metadata"]
    assert metadata["showroom"] is True
    assert metadata["operator_workshop"] is True
    assert metadata["content_only"] is True
    assert metadata["required_models"] == [lab["model"]]
    assert metadata["showroom_content_repo_url"] == (
        "https://github.com/rhpds/launchpad.git"
    )
    assert re.fullmatch(r"[0-9a-f]{40}", metadata["showroom_content_ref"])
    assert metadata["showroom_content_ref"] == "3d176f7ca76e80d424e3a2bd5168248d337ebeab"
    assert metadata["showroom_content_playbook"] == lab["playbook"]

    playbook = yaml.safe_load((ROOT / lab["playbook"]).read_text())
    assert playbook["site"]["start_page"] == "modules::index.adoc"
    assert playbook["content"]["sources"] == [
        {"url": ".", "start_path": lab["content_path"]}
    ]
    assert "rhdp_showroom_theme" in playbook["ui"]["bundle"]["url"]
    assert playbook["ui"]["supplemental_files"] == [
        {"path": "./content/supplemental-ui"}
    ]
    assert playbook["output"]["dir"] == "./www"

    component = yaml.safe_load((ROOT / lab["content_path"] / "antora.yml").read_text())
    assert component["title"] == lab["title"]
    assert component["asciidoc"]["attributes"]["project_name"] == "%namespace%"

    nav = ROOT / lab["content_path"] / "modules/ROOT/nav.adoc"
    index = ROOT / lab["content_path"] / "modules/ROOT/pages/index.adoc"
    assert nav.exists()
    assert index.exists()
    assert "xref:" in nav.read_text()


@pytest.mark.parametrize("lab", INTEL_GUIDED_LABS)
def test_intel_guided_lab_uses_launchpad_sso_instructions(lab):
    pages = ROOT / lab["content_path"] / "modules/ROOT/pages"
    content = "\n".join(path.read_text() for path in sorted(pages.glob("*.adoc")))

    assert "oc login -u {user} -p {password}" not in content
    assert "*Password:* `{password}`" not in content
    assert "Launchpad has already authenticated this terminal" in content
