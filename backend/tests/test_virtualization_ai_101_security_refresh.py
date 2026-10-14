from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVISION = "e881ece208528720974f4e7bc659a0c8ad0627fb"
IMAGES = {
    "workload_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-adapter@sha256:775377060ec11006604f458c887357e1fc32c71c3cdf89411719cd4e3eef3586",
    "presentation_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-presentation@sha256:723b28c736cac152e7872a8b5ec146f877ab1baf78b2e4375ce31a53e346c378",
}


def test_101_security_refresh_pins_one_exact_release():
    item = yaml.safe_load((ROOT / "catalog/virtualization-ai-foundations-101/catalog-item.yaml").read_text())
    intake = yaml.safe_load((ROOT / "catalog-onboarding/virtualization-ai-foundations-101.yaml").read_text())
    meta = item["metadata"]
    assert meta["showroom_content_ref"] == meta["workload_revision"] == REVISION
    assert all(source["revision"] == REVISION for source in intake["sources"].values())
    assert meta["showroom_content_image"] == intake["sources"]["showroom"]["content_image"]
    assert meta["showroom_content_image"].endswith("@sha256:8ab3bc87b6d5d7831c19a5fb7d37961bca1f4531f93f0ebc97ff59b9ed404731")
    for key, image in IMAGES.items():
        assert meta["workload_helm_values"][key] == intake["runtime"]["workload"]["helm_values"][key] == image
