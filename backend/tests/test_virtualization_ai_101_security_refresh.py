from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVISION = "49cfe274b7dc191f786b1c5d8ff9e37869dc8170"
IMAGES = {
    "workload_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-adapter@sha256:db4f9979a0dd2147d29120d8d32989b9ed3df6ef41c7d3f09c399b184d21146e",
    "presentation_image": "ghcr.io/jkershawrh/virtualization-ai-foundations-presentation@sha256:a7f4339792038c299f08a5bf5076b50fb3cbcd44176c5b3737ba908566078c04",
}


def test_101_security_refresh_pins_one_exact_release():
    item = yaml.safe_load((ROOT / "catalog/virtualization-ai-foundations-101/catalog-item.yaml").read_text())
    intake = yaml.safe_load((ROOT / "catalog-onboarding/virtualization-ai-foundations-101.yaml").read_text())
    meta = item["metadata"]
    assert meta["showroom_content_ref"] == meta["workload_revision"] == REVISION
    assert all(source["revision"] == REVISION for source in intake["sources"].values())
    assert meta["showroom_content_image"] == intake["sources"]["showroom"]["content_image"]
    assert meta["showroom_content_image"].endswith("@sha256:f2f134d9b5f35dd5833b729404176ef615466ad53062ab6c87dbbb30cde91190")
    for key, image in IMAGES.items():
        assert meta["workload_helm_values"][key] == intake["runtime"]["workload"]["helm_values"][key] == image
