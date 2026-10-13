from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVISION = "7079b405d380d531e9d7e33b41f66be88daa4c8c"
IMAGES = {
    "workload_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-adapter@sha256:b2063555da50c79c195ea4145dda4b5a339e18febc4fa9e2d8d0bab10cc0f289",
    "presentation_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-presentation@sha256:58a79075e9dde6e852314fcc60f4a292cde1939926bfdf0098a3817075162514",
}


def test_101_security_refresh_pins_one_exact_release():
    item = yaml.safe_load((ROOT / "catalog/virtualization-ai-foundations-101/catalog-item.yaml").read_text())
    intake = yaml.safe_load((ROOT / "catalog-onboarding/virtualization-ai-foundations-101.yaml").read_text())
    meta = item["metadata"]
    assert meta["showroom_content_ref"] == meta["workload_revision"] == REVISION
    assert all(source["revision"] == REVISION for source in intake["sources"].values())
    assert meta["showroom_content_image"] == intake["sources"]["showroom"]["content_image"]
    assert meta["showroom_content_image"].endswith("@sha256:aefbd49e58dbbbf42a854b5439668c828054e2dbbcc2233d77f3c63bc2d434ff")
    for key, image in IMAGES.items():
        assert meta["workload_helm_values"][key] == intake["runtime"]["workload"]["helm_values"][key] == image
