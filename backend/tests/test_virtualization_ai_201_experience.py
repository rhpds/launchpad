from pathlib import Path
import hashlib
import json

import yaml


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog/virtualization-ai-201/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/virtualization-ai-201.yaml"
CERTIFICATION = ROOT / "certification/catalog/virtualization-ai-201.yaml"
SOURCE_REVISION = "f5cbcad3865390d7d5844d94087b59eb94c8f276"
PRESENTATION_IMAGE = (
    "ghcr.io/jkershawrh/virtualization-ai-201-presentation@sha256:"
    "84a9b5ae29903ffedfc9b84753b362f5715167f23057628e99df5a94e1683a06"
)
ADAPTER_IMAGE = (
    "ghcr.io/jkershawrh/virtualization-ai-201-adapter@sha256:"
    "177af37c53b08b09c73b39b50bbaa92c47f2737c7072c2c14a3eed1e04bc9c99"
)
SHOWROOM_IMAGE = (
    "ghcr.io/jkershawrh/virtualization-ai-201-showroom-content@sha256:"
    "dc4f902c9892824e1eb9f1ddabc9bc4b56f7a4090da5a61a429116b857c30168"
)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_201_requires_vm_origin_and_truthful_live_inference_before_certification() -> None:
    catalog = _load(CATALOG)
    intake = _load(INTAKE)
    contract = _load(CERTIFICATION)
    metadata = catalog["metadata"]
    runtime = intake["runtime"]

    assert catalog["status"] == intake["catalog"]["status"] == "active"
    assert intake["certification"]["certified_seats"] == 1
    assert intake["certification"]["stage"] == "1-seat-certified"
    assert metadata["allowed_exposure_policies"] == ["internal", "public_code"]
    assert runtime["allowed_exposure_policies"] == ["internal", "public_code"]
    assert metadata["recommended_next_items"] == ["virtualization-ai-301"]
    assert intake["learning"]["recommended_next_items"] == ["virtualization-ai-301"]
    assert metadata["showroom_tabs"] == runtime["tabs"]
    assert metadata["showroom_tabs"][0] == {
        "id": "story",
        "title": "Story",
        "source": "workload.route.ui",
        "path": "/",
    }
    assert metadata["showroom_content_repo_url"].startswith(
        "https://github.com/"
    )
    assert metadata["workload_repo"].startswith("https://github.com/")
    for source in intake["sources"].values():
        assert source["gitops_repo_url"].startswith("https://github.com/")
        assert source["revision"] == SOURCE_REVISION
    assert metadata["showroom_content_ref"] == SOURCE_REVISION
    assert metadata["showroom_content_playbook"] == "default-site.yml"
    assert intake["sources"]["showroom"]["playbook"] == "default-site.yml"
    assert metadata["workload_revision"] == SOURCE_REVISION
    assert metadata["showroom_content_image"] == SHOWROOM_IMAGE
    assert metadata["workload_helm_values"]["presentation_image"] == PRESENTATION_IMAGE
    assert metadata["workload_helm_values"]["workload_image"] == ADAPTER_IMAGE
    # This receipt proves the current internal workload, not current public SSO.
    receipt = ROOT / metadata["source_references"]["certification_evidence"]
    assert hashlib.sha256(receipt.read_bytes()).hexdigest() == (
        receipt.with_suffix(".json.sha256").read_text().split()[0]
    )
    evidence = json.loads(receipt.read_text())
    probe = evidence["seat_results"][0]["probe"]["result"]
    assert evidence["result"] == "GREEN-live"
    assert probe["provenance"]["source_revision"] == SOURCE_REVISION
    assert probe["runtime_images"] == {
        "adapter": ADAPTER_IMAGE, "presentation": PRESENTATION_IMAGE
    }
    assert probe["journey"]["model_participated"] is True
    assert probe["journey"]["request_origin"] == "contract-author-vm"
    assert evidence["cleanup"]["status"] == "completed"
    assert all(value == 0 for value in evidence["cleanup"]["resource_counts"].values())

    expected_private = {
        "source": "generated_ssh_keypair",
        "pair": "contract-author-vm",
        "part": "private",
    }
    assert metadata["workload_runtime_secret_sources"]["VM_SSH_PRIVATE_KEY"] == (
        expected_private
    )
    assert runtime["workload"]["runtime_secret_sources"]["VM_SSH_PRIVATE_KEY"] == (
        expected_private
    )
    assert metadata["workload_runtime_value_bindings"] == {
        "vm.sshAuthorizedKey": "VM_SSH_PUBLIC_KEY"
    }
    assert runtime["workload"]["runtime_value_bindings"] == {
        "vm.sshAuthorizedKey": "VM_SSH_PUBLIC_KEY"
    }

    assert metadata["required_models"] == runtime["required_models"] == [
        "granite-3.2-8b-tools"
    ]
    assertions = contract["spec"]["seat_probe"]["json_assertions"]
    assert {"path": "journey.source_state", "equals": "LIVE"} in assertions
    assert {
        "path": "journey.request_origin",
        "equals": "contract-author-vm",
    } in assertions
    assert {"path": "journey.human_authority_preserved", "equals": True} in assertions
    assert {"path": "journey.model_participated", "equals": True} in assertions
    assert {
        "path": "journey.model",
        "equals": "granite-3.2-8b-tools",
    } in assertions
    assert metadata["activation_blockers"] == []
    assert metadata["certification_transfer"] == "none"
    assert metadata["activation_blockers"] == intake["certification"][
        "activation_blockers"
    ]

    driver = (ROOT / "scripts/certify-virtualization-ai-seat.sh").read_text()
    assert "terminal_contract_author_request()" in driver
    assert "contract_author_response" in driver
    assert "oc get vmi contract-author-vm" in driver
    assert 'learner@"$vm_ip"' in driver
    assert "wait_for_resource vm" in driver
    assert "wait_for_resource vmi" in driver
    assert "scp -i" not in driver
    assert "/home/learner/vm_client.py" in driver
    assert "normalize_remote_json" in driver
    assert "/home/learner/vm_client.py" in driver
    assert "normalize_remote_json()" in driver
    assert "JSONDecoder" in driver
