from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml

IMMUTABLE_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
CATALOG_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_REF = re.compile(r"image::([^\[]+)\[")
XREF = re.compile(r"xref:([^\[#]+)(?:#[^\[]+)?\[")
VALUE_PATH = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z][A-Za-z0-9_-]*)*$")
RUNTIME_TEMPLATE_FIELD = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")
SENSITIVE_RUNTIME_MARKERS = ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "PRIVATE_KEY")


def load_intake(path: Path | str) -> dict[str, Any]:
    """Load a repository-native catalog onboarding contract."""
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise TypeError(f"Catalog onboarding intake must be a YAML mapping: {path}")
    return data


def build_catalog_item(intake: dict[str, Any]) -> dict[str, Any]:
    """Generate the fail-closed catalog record controlled by an intake contract."""
    catalog = intake["catalog"]
    sources = intake["sources"]
    showroom = sources["showroom"]
    workload = sources["workload"]
    runtime = intake["runtime"]
    certification = intake["certification"]
    resources = runtime["seat_resources"]
    workload_contract = runtime.get("workload", {})
    references = intake.get("references", {})

    return {
        "catalog_item_id": catalog["catalog_item_id"],
        "display_name": catalog["display_name"],
        "description": catalog["description"],
        "category": catalog["category"],
        "version": catalog["version"],
        # Intake-generated catalog entries stay non-orderable until the
        # certification contract has no blockers and is explicitly promoted.
        "status": "draft",
        "required_capabilities": runtime["required_capabilities"],
        "default_hardware_profile": runtime.get("default_hardware_profile", "xeon-basic"),
        "default_quota_profile": runtime.get("default_quota_profile", "large"),
        "default_ttl": runtime.get("default_ttl", "4h"),
        "provisioner_refs": runtime.get("provisioner_refs", ["helm-workload", "showroom"]),
        "validation_refs": runtime.get(
            "validation_refs",
            [
                "pod-ready",
                "route-accessible",
                "inference-health",
                "agentops-journey",
            ],
        ),
        "observability_profile": runtime.get("observability_profile", "agentops-full-stack"),
        "supported_branding": catalog.get(
            "supported_branding", ["redhat-intel-default", "intel-internal"]
        ),
        "metadata": {
            "showroom": True,
            "operator_workshop": True,
            "content_only": False,
            "onboarding_managed": True,
            "onboarding_contract": intake.get(
                "onboarding_contract",
                f"catalog-onboarding/{catalog['catalog_item_id']}.yaml",
            ),
            "certification_stage": certification["stage"],
            "max_workshop_seats": certification["max_workshop_seats"],
            "promotion_sequence": certification["promotion_sequence"],
            "activation_blockers": certification["activation_blockers"],
            "showroom_journey": catalog["catalog_item_id"],
            "showroom_title": catalog["display_name"],
            "namespace_slug": runtime.get("namespace_slug", catalog["catalog_item_id"]),
            "showroom_content_repo_url": showroom["repo_url"],
            "showroom_content_ref": showroom["revision"],
            "showroom_content_playbook": showroom["playbook"],
            "showroom_content_start_path": showroom["start_path"],
            "showroom_tabs": runtime["tabs"],
            "required_models": runtime["required_models"],
            "inference_endpoint": runtime.get("inference_endpoint", "litellm"),
            "seat_cpu_millicores": resources["cpu_millicores"],
            "seat_memory_mib": resources["memory_mib"],
            "seat_pods": resources["pods"],
            "seat_storage_gib": resources["storage_gib"],
            "workload_repo": workload["repo_url"],
            "workload_revision": workload["revision"],
            "workload_deploy_type": runtime["deployment_type"],
            "workload_deployment_scope": runtime.get("deployment_scope", "seat"),
            "workload_deploy_path": workload["deploy_path"],
            "workload_source_kind": workload_contract.get("source_kind", "chart"),
            "workload_gitops_ready": bool(workload_contract.get("gitops_ready", False)),
            "workload_release_name": workload_contract.get(
                "release_name", catalog["catalog_item_id"]
            ),
            "workload_helm_values": workload_contract.get("helm_values", {}),
            "workload_runtime_secret_name": workload_contract.get("runtime_secret_name", ""),
            "workload_runtime_secret_sources": workload_contract.get("runtime_secret_sources", {}),
            "workload_runtime_secret_value_path": workload_contract.get(
                "runtime_secret_value_path", ""
            ),
            "workload_identity_value_path": workload_contract.get("identity_value_path", ""),
            "workload_routes": workload_contract.get("routes", {}),
            "workload_readiness": workload_contract.get("readiness", []),
            "source_content_repo": showroom["repo_url"],
            "source_content_revision": showroom["revision"],
            "source_references": references,
        },
    }


def _required_mapping(
    parent: dict[str, Any], key: str, errors: list[str], location: str
) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{location}.{key} must be a mapping")
        return {}
    return value


def _validate_contract(intake: dict[str, Any], errors: list[str]) -> None:
    if intake.get("api_version") != "launchpad.redhat.com/v1alpha1":
        errors.append("api_version must be launchpad.redhat.com/v1alpha1")

    catalog = _required_mapping(intake, "catalog", errors, "intake")
    sources = _required_mapping(intake, "sources", errors, "intake")
    runtime = _required_mapping(intake, "runtime", errors, "intake")
    certification = _required_mapping(intake, "certification", errors, "intake")
    showroom = _required_mapping(sources, "showroom", errors, "sources")
    workload = _required_mapping(sources, "workload", errors, "sources")

    catalog_id = str(catalog.get("catalog_item_id", ""))
    if not CATALOG_ID.fullmatch(catalog_id):
        errors.append("catalog.catalog_item_id must be a DNS-safe kebab-case ID")
    for key in ("display_name", "description", "category", "version"):
        if not str(catalog.get(key, "")).strip():
            errors.append(f"catalog.{key} is required")

    for source_name, source in (("showroom", showroom), ("workload", workload)):
        if not str(source.get("repo_url", "")).startswith("https://github.com/"):
            errors.append(f"sources.{source_name}.repo_url must be an HTTPS GitHub URL")
        revision = str(source.get("revision", ""))
        if not IMMUTABLE_GIT_SHA.fullmatch(revision):
            errors.append(
                f"sources.{source_name}.revision must be an immutable 40-character Git SHA"
            )

    references = intake.get("references", {})
    if references and not isinstance(references, dict):
        errors.append("references must be a mapping")
    elif isinstance(references, dict):
        for reference_name, reference in references.items():
            if not isinstance(reference, dict):
                errors.append(f"references.{reference_name} must be a mapping")
                continue
            if not str(reference.get("repo_url", "")).startswith("https://github.com/"):
                errors.append(f"references.{reference_name}.repo_url must be an HTTPS GitHub URL")
            if not IMMUTABLE_GIT_SHA.fullmatch(str(reference.get("revision", ""))):
                errors.append(
                    f"references.{reference_name}.revision must be an immutable 40-character Git SHA"
                )

    if runtime.get("deployment_type") not in {"helm", "kustomize", "manifests"}:
        errors.append("runtime.deployment_type must be helm, kustomize, or manifests")
    if not isinstance(runtime.get("required_capabilities"), list):
        errors.append("runtime.required_capabilities must be a list")
    if not isinstance(runtime.get("required_models"), list):
        errors.append("runtime.required_models must be a list")
    if runtime.get("deployment_scope", "seat") not in {"seat", "workshop"}:
        errors.append("runtime.deployment_scope must be seat or workshop")
    workload_contract = runtime.get("workload", {})
    if workload_contract and not isinstance(workload_contract, dict):
        errors.append("runtime.workload must be a mapping")
    elif isinstance(workload_contract, dict):
        identity_path = str(workload_contract.get("identity_value_path", ""))
        if identity_path and not VALUE_PATH.fullmatch(identity_path):
            errors.append("runtime.workload.identity_value_path must be a dotted Helm value path")

        secret_name = str(workload_contract.get("runtime_secret_name", ""))
        secret_path = str(workload_contract.get("runtime_secret_value_path", ""))
        if bool(secret_name) != bool(secret_path):
            errors.append(
                "runtime.workload runtime Secret name and value path must be declared together"
            )
        if secret_path and not VALUE_PATH.fullmatch(secret_path):
            errors.append(
                "runtime.workload.runtime_secret_value_path must be a dotted Helm value path"
            )

        readiness = workload_contract.get("readiness", [])
        if not isinstance(readiness, list):
            errors.append("runtime.workload.readiness must be a list")
        else:
            for index, check in enumerate(readiness):
                location = f"runtime.workload.readiness[{index}]"
                if not isinstance(check, dict):
                    errors.append(f"{location} must be a mapping")
                    continue
                for key in ("group", "version", "plural", "name", "condition_type"):
                    if not str(check.get(key, "")).strip():
                        errors.append(f"{location}.{key} is required")
                expected_status = str(check.get("expected_status", "True"))
                if expected_status not in {"True", "False", "Unknown"}:
                    errors.append(f"{location}.expected_status must be True, False, or Unknown")
                timeout = check.get("timeout_seconds", 300)
                if not isinstance(timeout, int) or timeout < 0:
                    errors.append(f"{location}.timeout_seconds must be a non-negative integer")

        secret_sources = workload_contract.get("runtime_secret_sources", {})
        if secret_sources and not isinstance(secret_sources, dict):
            errors.append("runtime.workload.runtime_secret_sources must be a mapping")
        elif isinstance(secret_sources, dict):
            source_keys = {str(key) for key in secret_sources}
            for raw_key, field_contract in secret_sources.items():
                key = str(raw_key)
                if isinstance(field_contract, str):
                    if field_contract not in {
                        "maas_api_key",
                        "maas_endpoint",
                        "requested_model",
                        "namespace",
                    }:
                        errors.append(
                            f"Runtime Secret field '{key}' uses unsupported source '{field_contract}'"
                        )
                    continue
                if not isinstance(field_contract, dict):
                    errors.append(f"Runtime Secret field '{key}' must be a source mapping")
                    continue
                declared = [
                    name for name in ("source", "value", "template") if name in field_contract
                ]
                if len(declared) != 1:
                    errors.append(
                        f"Runtime Secret field '{key}' must declare exactly one of source, value, or template"
                    )
                    continue
                if "value" in field_contract and any(
                    marker in key.upper() for marker in SENSITIVE_RUNTIME_MARKERS
                ):
                    errors.append(
                        f"Sensitive runtime field '{key}' cannot contain a catalog literal"
                    )
                if "source" in field_contract:
                    source = str(field_contract["source"])
                    if source not in {
                        "generated_password",
                        "maas_api_key",
                        "maas_endpoint",
                        "model_endpoint",
                        "requested_model",
                        "namespace",
                    }:
                        errors.append(
                            f"Runtime Secret field '{key}' uses unsupported source '{source}'"
                        )
                    if source == "generated_password":
                        length = field_contract.get("length", 32)
                        if not isinstance(length, int) or not 24 <= length <= 128:
                            errors.append(
                                f"Generated runtime field '{key}' length must be between 24 and 128"
                            )
                    if (
                        source == "model_endpoint"
                        and not str(field_contract.get("model", "")).strip()
                    ):
                        errors.append(
                            f"Runtime Secret field '{key}' using model_endpoint must declare model"
                        )
                if "template" in field_contract:
                    template = str(field_contract["template"])
                    fields = set(RUNTIME_TEMPLATE_FIELD.findall(template))
                    if not fields or not fields.issubset(source_keys):
                        errors.append(
                            f"Runtime Secret template for '{key}' references unknown fields"
                        )
    resources = _required_mapping(runtime, "seat_resources", errors, "runtime")
    for key in ("cpu_millicores", "memory_mib", "pods", "storage_gib"):
        value = resources.get(key)
        if not isinstance(value, int) or value < 0:
            errors.append(f"runtime.seat_resources.{key} must be a non-negative integer")

    tabs = runtime.get("tabs")
    if not isinstance(tabs, list) or not tabs:
        errors.append("runtime.tabs must contain at least one tab")
    elif len({tab.get("id") for tab in tabs if isinstance(tab, dict)}) != len(tabs):
        errors.append("runtime.tabs IDs must be unique")

    blockers = certification.get("activation_blockers")
    if not isinstance(blockers, list):
        errors.append("certification.activation_blockers must be a list")
    sequence = certification.get("promotion_sequence")
    if not isinstance(sequence, list) or not sequence or sequence[0] != 1:
        errors.append("certification.promotion_sequence must begin with one seat")


def _resolve_image(content_root: Path, page: Path, reference: str) -> bool:
    if reference.startswith(("http://", "https://", "data:")) or "{" in reference:
        return True
    candidates = [
        page.parent / reference,
        content_root / "modules/ROOT/images" / reference,
        content_root / "modules/ROOT/assets/images" / reference,
    ]
    return any(candidate.is_file() for candidate in candidates)


def _validate_showroom(
    source: Path, showroom: dict[str, Any], errors: list[str], warnings: list[str]
) -> None:
    errors_before_structure = len(errors)
    playbook_path = source / str(showroom.get("playbook", ""))
    content_root = source / str(showroom.get("start_path", ""))
    component_path = content_root / "antora.yml"
    nav_path = content_root / "modules/ROOT/nav.adoc"
    pages_dir = content_root / "modules/ROOT/pages"

    for label, path in (
        ("Showroom playbook", playbook_path),
        ("Antora component", component_path),
        ("Antora navigation", nav_path),
        ("Antora index", pages_dir / "index.adoc"),
    ):
        if not path.is_file():
            errors.append(f"{label} is missing: {path.relative_to(source)}")
    if len(errors) > errors_before_structure:
        return

    playbook = yaml.safe_load(playbook_path.read_text())
    sources = ((playbook or {}).get("content") or {}).get("sources") or []
    if not any(
        isinstance(entry, dict)
        and entry.get("url") == "."
        and entry.get("start_path") == showroom.get("start_path")
        for entry in sources
    ):
        errors.append("Showroom playbook does not select the declared local start_path")

    ui_bundle = (((playbook or {}).get("ui") or {}).get("bundle") or {}).get("url")
    if isinstance(ui_bundle, str) and "/latest/" in ui_bundle:
        warnings.append(
            "Showroom UI bundle uses a mutable latest URL; pin a release before activation"
        )

    pages = sorted(pages_dir.glob("*.adoc"))
    if not pages:
        errors.append("Showroom has no AsciiDoc pages")
        return

    nav = nav_path.read_text()
    for target in XREF.findall(nav):
        if not (pages_dir / target).is_file():
            errors.append(f"Showroom navigation references missing page: {target}")

    for page in pages:
        for image_ref in IMAGE_REF.findall(page.read_text()):
            image_ref = image_ref.strip()
            if not _resolve_image(content_root, page, image_ref):
                errors.append(f"Showroom page {page.name} references missing image: {image_ref}")

    if not (source / "ui-config.yml").is_file():
        warnings.append(
            "Source Showroom has no ui-config.yml; Launchpad must generate all runtime tabs"
        )


def _validate_workload(
    source: Path,
    workload: dict[str, Any],
    deployment_type: str,
    errors: list[str],
) -> None:
    deploy_path = source / str(workload.get("deploy_path", ""))
    if not deploy_path.is_dir():
        errors.append(f"Workload deploy path is missing: {deploy_path.relative_to(source)}")
        return
    required = {
        "helm": ("Chart.yaml", "values.yaml"),
        "kustomize": ("kustomization.yaml",),
        "manifests": (),
    }[deployment_type]
    for name in required:
        if not (deploy_path / name).is_file():
            errors.append(f"Workload {deployment_type} package is missing {name}")
    if deployment_type == "manifests" and not list(deploy_path.glob("*.y*ml")):
        errors.append("Workload manifest package contains no YAML files")


def validate_intake(
    intake: dict[str, Any],
    *,
    showroom_dir: Path | str | None = None,
    workload_dir: Path | str | None = None,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an intake and, when supplied, its checked-out source trees."""
    intake = copy.deepcopy(intake)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, str] = {}
    _validate_contract(intake, errors)
    checks["intake_contract"] = "pass" if not errors else "fail"

    if showroom_dir is not None and (intake.get("sources") or {}).get("showroom"):
        before = len(errors)
        _validate_showroom(Path(showroom_dir), intake["sources"]["showroom"], errors, warnings)
        checks["showroom_structure"] = "pass" if len(errors) == before else "fail"
    else:
        checks["showroom_structure"] = "not-run" if showroom_dir is None else "fail"

    if (
        workload_dir is not None
        and (intake.get("sources") or {}).get("workload")
        and (intake.get("runtime") or {}).get("deployment_type")
    ):
        before = len(errors)
        _validate_workload(
            Path(workload_dir),
            intake["sources"]["workload"],
            intake["runtime"]["deployment_type"],
            errors,
        )
        checks["workload_structure"] = "pass" if len(errors) == before else "fail"
    else:
        checks["workload_structure"] = "not-run" if workload_dir is None else "fail"

    if catalog is not None:
        if catalog == build_catalog_item(intake):
            checks["catalog_drift"] = "pass"
        else:
            checks["catalog_drift"] = "fail"
            errors.append("Generated catalog item differs from the committed catalog item")
    else:
        checks["catalog_drift"] = "not-run" if catalog is None else "fail"

    blockers = (intake.get("certification") or {}).get("activation_blockers") or []
    return {
        "catalog_item_id": (intake.get("catalog") or {}).get("catalog_item_id"),
        "validation_status": "pass" if not errors else "fail",
        "activation_status": "blocked" if blockers or errors else "eligible",
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "activation_blockers": blockers,
        "source_revisions": {
            name: source.get("revision")
            for name, source in (intake.get("sources") or {}).items()
            if isinstance(source, dict)
        },
    }
