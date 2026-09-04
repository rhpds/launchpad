import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence/intel-guided-content-single-seat-2026-09-04.json"


def _evidence():
    return json.loads(EVIDENCE.read_text())


def test_evidence_manifest_covers_all_native_intel_catalog_items():
    evidence = _evidence()

    assert evidence["schema_version"] == "1.0"
    assert len(evidence["commit_sha"]) == 40
    assert evidence["cluster"] == "arena"
    assert evidence["scope"] == "single-seat-native-content"
    assert {item["catalog_item_id"] for item in evidence["catalog_items"]} == {
        "intel-xeon6-agent-201",
        "intel-llm-cpu-serving",
        "intel-llm-tool-calling",
    }
    assert all(item["max_workshop_seats"] == 1 for item in evidence["catalog_items"])


def test_evidence_matrix_and_single_seat_rubric_are_green():
    evidence = _evidence()

    for row in evidence["validation_matrix"]:
        assert row["critical"] is True
        assert all(
            row[column] == "GREEN"
            for column in ("unit", "contract", "component", "bdd", "live", "cleanup")
        )
    assert evidence["rubric"]["score"] == 100
    assert sum(evidence["rubric"]["categories"].values()) == 100
    assert evidence["cleanup"]["matching_certification_namespaces"] == 0
    assert evidence["cleanup"]["matching_argocd_applications"] == 0
