from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _load_contract(level: str) -> dict:
    return yaml.safe_load(
        (ROOT / f"certification/catalog/sovereign-ai-{level}.yaml").read_text(
            encoding="utf-8"
        )
    )


def _page_paths(level: str) -> list[str]:
    return [
        page["path"]
        for page in _load_contract(level)["spec"]["showroom"]["pages"]
    ]


def test_sovereign_ai_101_certifies_the_complete_learner_journey() -> None:
    assert _page_paths("101") == [
        "/www/sovereign-ai-101/main/index.html",
        "/www/sovereign-ai-101/main/00-mission.html",
        "/www/sovereign-ai-101/main/01-connect.html",
        "/www/sovereign-ai-101/main/02-allow.html",
        "/www/sovereign-ai-101/main/03-protect.html",
        "/www/sovereign-ai-101/main/04-fail-closed.html",
        "/www/sovereign-ai-101/main/05-prove.html",
        "/www/sovereign-ai-101/main/06-decide.html",
        "/www/sovereign-ai-101/main/07-cleanup.html",
    ]


def test_sovereign_ai_201_certifies_the_complete_learner_journey() -> None:
    assert _page_paths("201") == [
        "/www/sovereign-ai-201/main/index.html",
        "/www/sovereign-ai-201/main/01-prerequisite.html",
        "/www/sovereign-ai-201/main/02-map-boundaries.html",
        "/www/sovereign-ai-201/main/03-author-contract.html",
        "/www/sovereign-ai-201/main/04-wire-controls.html",
        "/www/sovereign-ai-201/main/05-qualify-paths.html",
        "/www/sovereign-ai-201/main/06-break-fail-closed.html",
        "/www/sovereign-ai-201/main/07-evidence-authority.html",
        "/www/sovereign-ai-201/main/08-reclaim.html",
        "/www/sovereign-ai-201/main/99-conclusion.html",
    ]


def test_sovereign_ai_301_certifies_every_current_journey_page() -> None:
    assert _page_paths("301") == [
        "/www/sovereign-ai-301/main/index.html",
        "/www/sovereign-ai-301/main/00-mission.html",
        "/www/sovereign-ai-301/main/01-protection.html",
        "/www/sovereign-ai-301/main/02-challenge.html",
        "/www/sovereign-ai-301/main/03-appraise.html",
        "/www/sovereign-ai-301/main/04-release.html",
        "/www/sovereign-ai-301/main/05-failures.html",
        "/www/sovereign-ai-301/main/06-handoff.html",
        "/www/sovereign-ai-301/main/07-cleanup.html",
    ]


def test_sovereign_ai_301_is_presented_at_its_proven_internal_one_seat_limit() -> None:
    catalog = yaml.safe_load(
        (ROOT / "catalog/sovereign-ai-301/catalog-item.yaml").read_text(
            encoding="utf-8"
        )
    )
    metadata = catalog["metadata"]

    assert catalog["status"] == "active"
    assert metadata["certification_stage"] == "1-seat-certified"
    assert metadata["max_workshop_seats"] == 1
    assert metadata["activation_blockers"] == []
    assert metadata["allowed_exposure_policies"] == ["internal"]
    assert metadata["public_access_certification_stage"] == "not-certified"
