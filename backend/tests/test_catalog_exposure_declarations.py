"""Guard catalog exposure declarations against their certification scope.

Runtime exposure gating reads ``metadata.allowed_exposure_policies`` from the
catalog item and fails open when the field is absent. The certification
contract at ``certification/catalog/<id>.yaml`` is the authority for what an
item may expose, so a catalog item must never declare a policy its contract
does not authorise. Nothing enforced that before this test: six active items
had drifted, and the deployed Flightpath copy of ``intel-llm-cpu-serving``
was missing the declaration entirely while its base item had it.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = ROOT / "catalog"
CERTIFICATION_DIR = ROOT / "certification" / "catalog"
CANDIDATE_OVERLAY_DIR = (
    ROOT / "deploy" / "launchpad" / "overlays" / "flightpath-candidate"
)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _declared_exposure(document: dict) -> list[str]:
    return list((document.get("metadata") or {}).get("allowed_exposure_policies") or [])


def test_catalog_exposure_is_within_certified_scope() -> None:
    mismatches = []
    for item_path in sorted(CATALOG_DIR.glob("*/catalog-item.yaml")):
        item = _load(item_path)
        catalog_item_id = item.get("catalog_item_id")
        contract_path = CERTIFICATION_DIR / f"{catalog_item_id}.yaml"
        if not catalog_item_id or not contract_path.exists():
            continue
        declared = set(_declared_exposure(item))
        certified = set(
            (contract_path.exists() and _load(contract_path).get("spec") or {}).get(
                "allowed_exposure_policies"
            )
            or []
        )
        undeclared_scope = declared - certified
        if undeclared_scope:
            mismatches.append((catalog_item_id, sorted(undeclared_scope)))
    assert mismatches == [], (
        "catalog exposes policies its certification contract does not authorise: "
        f"{mismatches}"
    )


def test_deployed_overlay_catalog_copies_match_their_base_item() -> None:
    """The candidate overlay ships full copies of some catalog items.

    A copy that omits ``allowed_exposure_policies`` is not merely cosmetic:
    the overlay ConfigMap is the deployed source for that item, so the cluster
    falls back to the fail-open default even when the base item declares an
    explicit policy.
    """

    mismatches = []
    for overlay_path in sorted(CANDIDATE_OVERLAY_DIR.glob("*.catalog-item.yaml")):
        name = overlay_path.name[: -len(".catalog-item.yaml")]
        base_path = CATALOG_DIR / name / "catalog-item.yaml"
        if not base_path.exists():
            continue
        overlay_exposure = _declared_exposure(_load(overlay_path))
        base_exposure = _declared_exposure(_load(base_path))
        if overlay_exposure != base_exposure:
            mismatches.append((name, overlay_exposure, base_exposure))
    assert mismatches == [], (
        "deployed overlay catalog copies disagree with their base item on "
        f"allowed_exposure_policies: {mismatches}"
    )
