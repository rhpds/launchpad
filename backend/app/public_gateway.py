from __future__ import annotations

import html
import os
from datetime import datetime
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Launchpad Public Access Gateway", docs_url=None, redoc_url=None, openapi_url=None)
BACKEND = os.getenv("LAUNCHPAD_INTERNAL_API", "http://backend:8000/api/v1").rstrip("/")
BROKER_KEY = os.getenv("ACCESS_BROKER_KEY", "")
UPSTREAM_TLS_VERIFY = os.getenv("PUBLIC_UPSTREAM_TLS_VERIFY", "true").casefold() not in {"0", "false", "no"}


def _host(request: Request) -> str:
    return request.headers.get("host", "").split(":", 1)[0].casefold()


def _username(request: Request) -> str:
    # oauth2-proxy always uses the OIDC subject for X-Forwarded-User.  The
    # configured email claim carries Launchpad's stable preferred_username.
    return request.headers.get("x-forwarded-email", "") or request.headers.get("x-forwarded-user", "")


async def _resolve(request: Request) -> dict:
    username = _username(request)
    cookie = request.cookies.get("launchpad_access", "")
    async with httpx.AsyncClient(timeout=10) as client:
        if username:
            result = await client.get(
                f"{BACKEND}/public-access/private/resolve-identity",
                params={"host": _host(request), "username": username},
                headers={"X-Access-Broker-Key": BROKER_KEY},
            )
        else:
            result = await client.get(
                f"{BACKEND}/public-access/private/resolve",
                params={"host": _host(request)},
                headers={"X-Access-Broker-Key": BROKER_KEY},
                cookies={"launchpad_access": cookie},
            )
    if result.status_code != 200:
        raise HTTPException(result.status_code, "Access denied")
    return result.json()


def _page(body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html><head><meta name=viewport content='width=device-width,initial-scale=1'><title>Intel × Red Hat AI Launchpad</title><style>
    :root{{--red:#ee0000;--blue:#0071c5;--panel:#212121;--muted:#b8bbbe}}*{{box-sizing:border-box}}body{{font:16px 'Red Hat Text',system-ui,sans-serif;background:radial-gradient(circle at 15% 0,#3b1717 0,transparent 34%),radial-gradient(circle at 90% 20%,#102c43 0,transparent 30%),#151515;color:#fff;margin:0;min-height:100vh}}header{{height:68px;border-bottom:1px solid #353535;background:rgba(21,21,21,.94);display:flex;align-items:center;justify-content:space-between;padding:0 max(24px,calc((100vw - 1120px)/2))}}.brand{{display:flex;align-items:center;gap:12px;font-weight:750;letter-spacing:.01em}}.brand-red{{color:var(--red)}}.brand-intel{{color:#59b8ee}}nav{{display:flex;align-items:center;gap:8px}}nav a{{color:var(--muted);padding:9px 12px;text-decoration:none;border-radius:6px}}nav a:hover{{color:#fff;background:#ffffff12}}main{{max-width:1040px;margin:0 auto;padding:64px 24px 80px}}.panel,section{{background:rgba(33,33,33,.96);border:1px solid #3c3c3c;border-radius:12px;padding:28px;margin-top:20px;box-shadow:0 18px 50px #0005}}h1{{font-size:clamp(30px,5vw,46px);line-height:1.08;margin:0 0 12px}}h2{{margin:0 0 8px}}p{{color:var(--muted);line-height:1.55}}.actions{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:24px}}a.button,button{{display:block;background:var(--red);color:#fff;border:0;border-radius:6px;padding:13px 18px;font-weight:700;text-align:center;text-decoration:none;cursor:pointer}}a.secondary{{background:#2b2b2b;border:1px solid #555}}input{{width:100%;background:#151515;color:#fff;border:1px solid #777;border-radius:6px;padding:13px;margin:7px 0 12px}}small{{display:block;color:#8d9092;margin-top:20px}}.eyebrow{{color:#59b8ee;text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.12em}}@media(max-width:700px){{header{{height:auto;padding:18px 22px;align-items:flex-start;gap:15px;flex-direction:column}}main{{padding-top:40px}}}}
    </style></head><body><header><div class='brand'><span class='brand-red'>Red Hat</span><span>×</span><span class='brand-intel'>intel</span><span>AI Launchpad</span></div><nav><a href='/'>Current lab</a><a href='/my-labs'>My Lab Access</a><a href='/oauth2/sign_out?rd=%2Frealms%2Flaunchpad-public%2Fprotocol%2Fopenid-connect%2Flogout'>Switch participant</a></nav></header><main><div class='eyebrow'>Participant workspace</div><div class='panel'>{body}</div></main></body></html>""")


async def _labs_for(username: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{BACKEND}/public-access/private/identity-entitlements",
            params={"username": username},
            headers={"X-Access-Broker-Key": BROKER_KEY},
        )
    if response.status_code != 200:
        return []
    return response.json().get("labs", [])


def _lab_cards(labs: list[dict]) -> str:
    if not labs:
        return "<p>No active labs are associated with this account.</p>"
    cards = []
    for lab in labs:
        label = html.escape(lab.get("catalog_slug") or "Lab environment")
        url = html.escape(lab["public_url"], quote=True)
        expiry = html.escape(str(lab["expires_at"]))
        cards.append(f"<section><h2>{label}</h2><p>Available until {expiry}</p><div class='actions'><a class='button' href='{url}'>Resume lab</a></div></section>")
    return "".join(cards)


@app.get("/health")
def health():
    return {"status": "ok", "service": "public-access-gateway"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = _username(request)
    try:
        target = await _resolve(request)
    except HTTPException:
        if username:
            return _page(
                "<h1>Add this lab</h1><p>You are already signed in. Enter only this lab's instructor code.</p>"
                "<form method=post action=/add-lab><input name=code required autocomplete=one-time-code "
                "placeholder='Instructor code'><button>Add lab</button></form><a href='/my-labs'>My Lab Access</a>"
            )
        return _page("<h1>Join your lab</h1><p>Enter the email label and code supplied by your instructor.</p><small>Email ownership is not verified. The instructor code is the sole secret.</small><form method=post action=/claim><input name=email type=email required placeholder='Email'><input name=code required autocomplete=one-time-code placeholder='Instructor code'><button>Join lab</button></form>")
    links = []
    for key, label in (("showroom_url", "Open visual guide"), ("workspace_url", "Open workspace"), ("console_url", "Open OpenShift Console")):
        if target.get(key):
            path = "/proxy/" + key.removesuffix("_url") + "/"
            links.append(f"<a class='button' href='{path}'>{html.escape(label)}</a>")
    return _page(f"<h1>Your lab is ready</h1><p>Seat <strong>{html.escape(target['seat_ref'])}</strong></p><div class='actions'>{''.join(links)}<a class='button secondary' href='/my-labs'>My Lab Access</a></div><small>Access ends at {html.escape(str(target['expires_at']))}.</small>")


@app.get("/my-labs", response_class=HTMLResponse)
async def my_labs(request: Request):
    username = _username(request)
    if not username:
        return RedirectResponse("/", status_code=302)
    return _page(
        "<h1>My Lab Access</h1><p>Resume any active environment associated with your participant identity.</p>"
        + _lab_cards(await _labs_for(username))
        + "<small>To add another lab, open its instructor-provided link and enter that lab's code.</small>"
    )


@app.post("/add-lab")
async def add_lab(request: Request, code: str = Form()):
    username = _username(request)
    if not username:
        return RedirectResponse("/", status_code=303)
    async with httpx.AsyncClient(timeout=15) as client:
        result = await client.post(
            f"{BACKEND}/public-access/private/claim-identity",
            json={"host": _host(request), "username": username, "code": code},
            headers={"X-Access-Broker-Key": BROKER_KEY},
        )
    if result.status_code != 200:
        return _page("<h1>Access denied</h1><p>Access request cannot be completed. Check the instructor code.</p><a href='/my-labs'>My Lab Access</a>")
    return RedirectResponse("/", status_code=303)


@app.post("/claim")
async def claim(request: Request, email: str = Form(), code: str = Form()):
    host = _host(request)
    async with httpx.AsyncClient(timeout=15) as client:
        policy = await client.get(f"{BACKEND}/public-access/private/order-by-host", params={"host": host}, headers={"X-Access-Broker-Key": BROKER_KEY})
        if policy.status_code != 200:
            return _page("<h1>Access denied</h1><p>Access request cannot be completed.</p>")
        result = await client.post(f"{BACKEND}/public-access/claim", json={"order_id": policy.json()["order_id"], "email": email, "code": code})
    if result.status_code != 200:
        return _page("<h1>Access denied</h1><p>Access request cannot be completed. Check the instructor code.</p>")
    response = RedirectResponse("/", status_code=303)
    cookie = result.cookies.get("launchpad_access")
    if cookie:
        expiry = datetime.fromisoformat(result.json()["session_expires_at"])
        response.set_cookie(
            "launchpad_access", cookie, httponly=True, secure=True, samesite="lax", path="/",
            max_age=max(1, int((expiry - datetime.utcnow()).total_seconds())),
        )
    return response


@app.get("/proxy/{kind}/{path:path}")
async def proxy(kind: str, path: str, request: Request):
    if kind not in {"showroom", "workspace", "console"}:
        raise HTTPException(404)
    target = await _resolve(request)
    base = target.get(f"{kind}_url")
    if not base:
        raise HTTPException(404)
    if kind == "console":
        return RedirectResponse(base, status_code=302)
    url = urljoin(base.rstrip("/") + "/", path)
    async with httpx.AsyncClient(timeout=30, follow_redirects=False, verify=UPSTREAM_TLS_VERIFY) as client:
        upstream = await client.request(request.method, url, params=request.query_params, headers={"accept": request.headers.get("accept", "*/*")})
    excluded = {"content-length", "connection", "transfer-encoding", "set-cookie"}
    return Response(upstream.content, status_code=upstream.status_code, headers={k: v for k, v in upstream.headers.items() if k.casefold() not in excluded})
