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


def test_virtualization_ai_201_certifies_the_complete_learner_journey() -> None:
    assert _page_paths("virtualization-ai-201") == [
        "/www/virtualization-ai-201/main/index.html",
        "/www/virtualization-ai-201/main/01-prerequisite.html",
        "/www/virtualization-ai-201/main/02-frame.html",
        "/www/virtualization-ai-201/main/03-author.html",
        "/www/virtualization-ai-201/main/04-wire.html",
        "/www/virtualization-ai-201/main/05-prove.html",
        "/www/virtualization-ai-201/main/06-break.html",
        "/www/virtualization-ai-201/main/07-evidence-reclaim.html",
        "/www/virtualization-ai-201/main/99-conclusion.html",
    ]


def test_virtualization_ai_301_certifies_the_complete_learner_journey() -> None:
    assert _page_paths("virtualization-ai-301") == [
        "/www/virtualization-ai-301/main/index.html",
        "/www/virtualization-ai-301/main/01-prerequisites.html",
        "/www/virtualization-ai-301/main/02-declare.html",
        "/www/virtualization-ai-301/main/03-observe.html",
        "/www/virtualization-ai-301/main/04-compare.html",
        "/www/virtualization-ai-301/main/05-refuse.html",
        "/www/virtualization-ai-301/main/06-review.html",
        "/www/virtualization-ai-301/main/07-reclaim.html",
        "/www/virtualization-ai-301/main/99-conclusion.html",
    ]
