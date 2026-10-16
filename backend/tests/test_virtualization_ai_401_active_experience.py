import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog/virtualization-ai-401/catalog-item.yaml"
INTAKE = ROOT / "catalog-onboarding/virtualization-ai-401.yaml"
CERTIFICATION = ROOT / "certification/catalog/virtualization-ai-401.yaml"
EVIDENCE = ROOT / (
    "evidence/runs/"
    "flightpath-live-20261002-virtualization-ai-401-public-1seat-r1.json"
)


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_401_active_experience_is_exact_truthful_and_one_seat_certified() -> None:
    catalog = _yaml(CATALOG)
    intake = _yaml(INTAKE)
    contract = _yaml(CERTIFICATION)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    metadata = catalog["metadata"]
    revision = "69e57566be66e87da4d9889c9057158fd171dc73"

    assert catalog["status"] == intake["catalog"]["status"] == "active"
    assert metadata["certification_stage"] == intake["certification"]["stage"] == (
        "1-seat-certified"
    )
    assert intake["certification"]["certified_seats"] == 1
    assert metadata["allowed_exposure_policies"] == intake["runtime"][
        "allowed_exposure_policies"
    ] == ["internal", "public_code"]
    assert metadata["public_access_certification_stage"] == "one-seat-certified"
    assert metadata["public_max_workshop_seats"] == 1
    assert metadata["showroom_content_ref"] == metadata["workload_revision"] == revision
    assert intake["sources"]["showroom"]["revision"] == revision
    assert intake["sources"]["workload"]["revision"] == revision
    assert metadata["required_models"] == intake["runtime"]["required_models"] == []
    assert metadata["inference_endpoint"] == "none"
    assert metadata["workload_runtime_secret_sources"] == {}
    assert [tab["id"] for tab in metadata["showroom_tabs"]] == [
        "story",
        "terminal",
        "openshift-console",
    ]

    references = metadata["source_references"]
    assert references["release_workflow"] == (
        "https://github.com/jkershawrh/virtualization-ai-401/actions/runs/38480912766"
    )
    assert references["historical_public_certification_evidence"] == str(EVIDENCE.relative_to(ROOT))
    assert references["current_public_browser_validation"] == "pending"
    current_path = ROOT / references["certification_evidence"]
    assert intake["references"]["certification_evidence"] == references["certification_evidence"]
    assert hashlib.sha256(current_path.read_bytes()).hexdigest() == current_path.with_suffix(".json.sha256").read_text().split()[0]
    current = json.loads(current_path.read_text())
    assert current["result"] == "GREEN-live"
    assert current["rubric"]["score"] == 100
    assert current["plan"]["seats"] == 1
    assert all(current["gates"].values())
    probe = current["seat_results"][0]["probe"]["result"]
    assert probe["provenance"]["source_revision"] == revision
    assert probe["restart_evidence_preserved"] is True
    assert probe["readiness"]["vmis_ready"] == 1
    assert probe["journey"]["model_participated"] is False
    assert probe["journey"]["human_authority_preserved"] is True
    for image in probe["runtime_images"].values():
        assert image.split("@", 1)[1] in str(metadata["workload_helm_values"])
    assert current["cleanup"]["model_keys_revoked"] is True
    assert all(value == 0 for value in current["cleanup"]["resource_counts"].values())
    # The remaining assertions preserve historical public-browser coverage only.
    assertions = contract["spec"]["seat_probe"]["json_assertions"]
    assert {"path": "journey.outcome", "equals": "ALLOW_REVIEW"} in assertions

    expected_hash = EVIDENCE.with_suffix(".json.sha256").read_text().split()[0]
    assert hashlib.sha256(EVIDENCE.read_bytes()).hexdigest() == expected_hash
    result = evidence["seat_results"][0]["probe"]["result"]
    assert evidence["result"] == "GREEN-live"
    assert evidence["rubric"]["score"] == 100
    assert result["journey"]["source_state"] == "REHEARSAL"
    assert result["journey"]["outcome"] == "ALLOW_REVIEW"
    assert result["journey"]["model_participated"] is False
    assert result["journey"]["human_authority_preserved"] is True
    assert result["readiness"]["vms_running"] == 1
    assert result["readiness"]["vmis_ready"] == 1
    assert evidence["security"]["contains_plaintext_credentials"] is False
    public_browser = evidence["seat_results"][0]["public_browser"]
    for gate in (
        "trusted_tls",
        "claim_succeeded",
        "same_seat_recovery_succeeded",
        "showroom_loaded",
        "showroom_antora_content_loaded",
        "story_embedded",
        "terminal_page_loaded",
        "terminal_token_entitlement_revalidated",
        "terminal_websocket_handshake",
        "openshift_console_embedded",
        "participant_identity_namespace_scoped",
        "cross_namespace_access_denied",
        "cluster_node_access_denied",
    ):
        assert public_browser[gate] is True
    assert evidence["cleanup"]["status"] == "completed"
    assert all(count == 0 for count in evidence["cleanup"]["resource_counts"].values())
