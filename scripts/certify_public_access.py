"""Disposable live certification harness for passwordless public lab access.

This runs the production Launchpad API in OpenShift mode, seeds exactly one
short-lived order/session pair, and adds an OIDC callback that exchanges the
authorization code. It is intentionally environment-driven and must only be
used with an isolated, labeled certification namespace.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

import httpx
import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse

from app.domain.enums import SessionStatus
from app.domain.models import LabSession


ORDER_ID = os.environ["CERT_ORDER_ID"]
NAMESPACE = os.environ["CERT_NAMESPACE"]
CALLBACK_BASE = os.environ["CERT_CALLBACK_BASE"].rstrip("/")
KEYCLOAK_BASE = os.environ["CERT_KEYCLOAK_BASE"].rstrip("/")
CLIENT_ID = os.environ.get("CERT_OIDC_CLIENT_ID", "launchpad-public-gateway")
CLIENT_SECRET = os.environ["CERT_OIDC_CLIENT_SECRET"]
TTL_MINUTES = int(os.environ.get("CERT_TTL_MINUTES", "60"))

# Import after environment validation so app.api.deps constructs its services
# with the caller-supplied OpenShift cluster configuration.
from app.api.deps import provisioning_service, public_access_service  # noqa: E402
from app.main import app  # noqa: E402


expires_at = datetime.utcnow() + timedelta(minutes=TTL_MINUTES)
session = LabSession(
    request_id=ORDER_ID,
    tenant_id="public-certification",
    catalog_item_id="openshift-developer-sandbox",
    namespace=NAMESPACE,
    cluster_ref="arena",
    status=SessionStatus.READY,
    lab_url=f"https://console-openshift-console.apps.arena.fm2aihpcsed.com/topology/ns/{NAMESPACE}",
    dashboard_url=f"https://console-openshift-console.apps.arena.fm2aihpcsed.com/topology/ns/{NAMESPACE}",
    started_at=datetime.utcnow(),
    expires_at=expires_at,
    metadata={"certification_only": True},
)
provisioning_service._sessions[session.session_id] = session
policy, one_time_code = public_access_service.create_policy(
    order_id=ORDER_ID,
    order_type="individual",
    catalog_slug="arena-access-certification",
    seat_refs=[ORDER_ID],
    expires_at=expires_at,
)


@app.get("/oauth2/callback", response_class=HTMLResponse)
async def certification_callback(request: Request, code: str = "", error: str = ""):
    if error or not code:
        return HTMLResponse("<h1>Access denied</h1><p>The certification login did not complete.</p>", status_code=403)
    redirect_uri = f"{CALLBACK_BASE}/oauth2/callback"
    async with httpx.AsyncClient(timeout=15) as client:
        token = await client.post(
            f"{KEYCLOAK_BASE}/realms/launchpad-public/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": redirect_uri,
            },
        )
    if token.status_code != 200:
        return HTMLResponse("<h1>Access denied</h1><p>The identity token could not be verified.</p>", status_code=403)
    claims = token.json()
    access_token = claims.get("access_token", "")
    async with httpx.AsyncClient(timeout=15) as client:
        userinfo = await client.get(
            f"{KEYCLOAK_BASE}/realms/launchpad-public/protocol/openid-connect/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    username = userinfo.json().get("preferred_username", "participant") if userinfo.status_code == 200 else "participant"
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'><title>Lab access verified</title>"
        "<style>body{margin:0;background:#151515;color:#f5f5f5;font:16px system-ui;display:grid;place-items:center;min-height:100vh}"
        ".card{width:min(520px,calc(100vw - 48px));background:#212427;padding:40px;border-radius:16px;box-shadow:0 18px 48px #0008}"
        "h1{margin:0 0 12px}code{color:#73bcf7}.ok{color:#3e8635;font-weight:700}</style></head><body><main class='card'>"
        "<p class='ok'>Identity and entitlement verified</p><h1>Arena lab access is ready</h1>"
        f"<p>Signed in as <code>{username}</code>.</p><p>Namespace: <code>{NAMESPACE}</code></p>"
        "<p>The remaining certification check confirms this identity can edit only the assigned namespace.</p>"
        "</main></body></html>"
    )


if __name__ == "__main__":
    print(f"CERT_ORDER_ID={ORDER_ID}", flush=True)
    print(f"CERT_PUBLIC_URL={policy.public_url}", flush=True)
    print(f"CERT_ONE_TIME_CODE={one_time_code}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("CERT_PORT", "18081")))
