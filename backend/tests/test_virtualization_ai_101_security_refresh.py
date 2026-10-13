from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVISION = "3f622615f544c75db87a37833fc209b3d1b60731"
IMAGES = {
    "workload_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-adapter@sha256:8046e653246f5cf6d35bbc841cf10a405c76a79d6d94b4c9ac47ca6781b57cf7",
    "presentation_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-presentation@sha256:205fb61bf069e59ce84817d5b69abbfc9f9bf3dd224206d29287b811af98368b",
}


def test_101_security_refresh_pins_one_exact_release():
    item = yaml.safe_load((ROOT / "catalog/virtualization-ai-foundations-101/catalog-item.yaml").read_text())
    intake = yaml.safe_load((ROOT / "catalog-onboarding/virtualization-ai-foundations-101.yaml").read_text())
    meta = item["metadata"]
    assert meta["showroom_content_ref"] == meta["workload_revision"] == REVISION
    assert all(source["revision"] == REVISION for source in intake["sources"].values())
    assert meta["showroom_content_image"] == intake["sources"]["showroom"]["content_image"]
    assert meta["showroom_content_image"].endswith("@sha256:b3db1c123fa309d25fb3df00fc1f4ef6f60b8da9c741d52c0f0313ccf23ed9b3")
    for key, image in IMAGES.items():
        assert meta["workload_helm_values"][key] == intake["runtime"]["workload"]["helm_values"][key] == image
