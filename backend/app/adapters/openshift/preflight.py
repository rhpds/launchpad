from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from app.domain.models import CatalogItem

logger = logging.getLogger("launchpad.preflight")


class PreflightCheck(BaseModel):
    name: str
    status: str  # pass, fail, skip
    message: str


class PreflightResult(BaseModel):
    passed: bool
    checks: List[PreflightCheck] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LiteLLMPreflightChecker:

    def __init__(self, api_base: str, api_key: str = "") -> None:
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key

    def check(
        self,
        catalog_item: CatalogItem,
        model_endpoints: Optional[Dict[str, str]] = None,
    ) -> PreflightResult:
        required_models = catalog_item.metadata.get("required_models", [])
        if not required_models:
            return PreflightResult(passed=True, checks=[])

        checks: List[PreflightCheck] = []
        endpoint_groups: Dict[str, List[str]] = {}
        for model in required_models:
            if model_endpoints is not None:
                endpoint = model_endpoints.get(model, "").rstrip("/")
                if not endpoint:
                    checks.append(PreflightCheck(
                        name=f"model:{model}",
                        status="fail",
                        message=f"No endpoint configured for model {model} on selected cluster",
                    ))
                    continue
            else:
                endpoint = self._api_base
            endpoint_groups.setdefault(endpoint, []).append(model)

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        for endpoint, models in endpoint_groups.items():
            try:
                resp = httpx.get(f"{endpoint}/models", timeout=10, headers=headers)
                resp.raise_for_status()
                available = {m["id"] for m in resp.json().get("data", [])}
            except Exception as exc:
                logger.warning("Model endpoint unreachable at %s: %s", endpoint, exc)
                checks.extend(
                    PreflightCheck(
                        name=f"model:{model}",
                        status="fail",
                        message=f"Model endpoint unreachable at {endpoint}: connection error",
                    )
                    for model in models
                )
                continue

            for model in models:
                if model in available:
                    checks.append(PreflightCheck(
                        name=f"model:{model}",
                        status="pass",
                        message=f"Model {model} available at {endpoint}",
                    ))
                else:
                    checks.append(PreflightCheck(
                        name=f"model:{model}",
                        status="fail",
                        message=f"Model {model} not found at {endpoint}",
                    ))

        passed = all(c.status == "pass" for c in checks)
        return PreflightResult(passed=passed, checks=checks)


class MockPreflightAdapter:

    def check(
        self,
        catalog_item: CatalogItem,
        model_endpoints: Optional[Dict[str, str]] = None,
    ) -> PreflightResult:
        return PreflightResult(passed=True, checks=[])
