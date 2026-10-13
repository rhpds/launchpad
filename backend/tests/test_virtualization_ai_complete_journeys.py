from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _page_paths(catalog_id: str) -> list[str]:
    contract = yaml.safe_load(
        (ROOT / f"certification/catalog/{catalog_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    return [page["path"] for page in contract["spec"]["showroom"]["pages"]]


def test_virtualization_ai_101_certifies_the_complete_learner_journey() -> None:
    assert _page_paths("virtualization-ai-foundations-101") == [
        "/www/virtualization-ai-101/main/index.html",
        "/www/virtualization-ai-101/main/01-verify.html",
        "/www/virtualization-ai-101/main/02-trace.html",
        "/www/virtualization-ai-101/main/03-invoke.html",
        "/www/virtualization-ai-101/main/04-inspect.html",
        "/www/virtualization-ai-101/main/05-failure.html",
        "/www/virtualization-ai-101/main/06-evidence.html",
        "/www/virtualization-ai-101/main/07-cleanup.html",
        "/www/virtualization-ai-101/main/99-conclusion.html",
    ]
