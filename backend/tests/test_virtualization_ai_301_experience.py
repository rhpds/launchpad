from pathlib import Path
import hashlib
import json

import yaml

from app.services.catalog_onboarding import build_catalog_item, load_intake


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog/virtualization-ai-301/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/virtualization-ai-301.yaml"
CERTIFICATION = ROOT / "certification/catalog/virtualization-ai-301.yaml"
DRIVER = ROOT / "scripts/certify-virtualization-ai-seat.sh"


def test_virtualization_ai_301_is_an_exact_one_seat_certified_rehearsal_candidate() -> None:
    intake = load_intake(INTAKE)
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    metadata = catalog["metadata"]

    assert catalog == build_catalog_item(intake)
    assert catalog["status"] == "active"
    assert metadata["certification_stage"] == "1-seat-certified"
    assert metadata["certification_transfer"] == "none"
    assert metadata["max_workshop_seats"] == 1
    assert intake["certification"]["certified_seats"] == 1
    assert catalog["validation_refs"] == ["pod-ready", "route-accessible"]
    assert metadata["showroom_content_ref"] == (
        "e5888aeac1042cbcf909b540eee1281fdc3c4dac"
    )
    assert metadata["source_content_revision"] == metadata["showroom_content_ref"]
    assert metadata["workload_revision"] == metadata["showroom_content_ref"]
    assert metadata["workload_helm_values"]["default_source_state"] == "REHEARSAL"
    assert metadata["activation_blockers"] == []
    assert metadata["allowed_exposure_policies"] == ["internal", "public_code"]
    # Current internal evidence must bind the release; historical public evidence
    # is not silently transferred by this regression check.
    receipt = ROOT / metadata["source_references"]["certification_evidence"]
    assert hashlib.sha256(receipt.read_bytes()).hexdigest() == (
        receipt.with_suffix(".json.sha256").read_text().split()[0]
    )
    evidence = json.loads(receipt.read_text())
    probe = evidence["seat_results"][0]["probe"]["result"]
    assert evidence["result"] == "GREEN-live"
    assert probe["provenance"]["source_revision"] == metadata["workload_revision"]
    assert probe["journey"]["source_state"] == "REHEARSAL"
    assert probe["journey"]["model_participated"] is False
    assert probe["placement_receipt"]["kubevirt_vmx"] is True
    values = metadata["workload_helm_values"]
    for component in ("adapter", "presentation"):
        image = values[component]["image"]
        assert probe["runtime_images"][component] == f"{image['repository']}@{image['digest']}"
    assert evidence["cleanup"]["status"] == "completed"
    assert all(value == 0 for value in evidence["cleanup"]["resource_counts"].values())


def test_virtualization_ai_301_certification_preserves_rehearsal_model_truth_and_platform_placement_proof() -> None:
    contract = yaml.safe_load(CERTIFICATION.read_text(encoding="utf-8"))
    assertions = contract["spec"]["seat_probe"]["json_assertions"]

    for expected in (
        {"path": "journey.source_state", "equals": "REHEARSAL"},
        {"path": "journey.model_participated", "equals": False},
        {"path": "journey.intel_placement_verified", "equals": True},
        {"path": "journey.human_authority_preserved", "equals": True},
        {"path": "placement_receipt.architecture", "equals": "amd64"},
        {"path": "placement_receipt.kubevirt_vmx", "equals": True},
        {
            "path": "placement_receipt.source",
            "equals": "platform-node-and-vmi-status",
        },
    ):
        assert expected in assertions

    driver = DRIVER.read_text(encoding="utf-8")
    assert 'model_participated:(if $catalog_id == "virtualization-ai-301" then false' in driver
    assert "status.nodeName" in driver
    assert "cpu-feature\\.node\\.kubevirt\\.io/vmx" in driver
    assert "platform-node-and-vmi-status" in driver
