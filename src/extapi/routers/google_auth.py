import base64
import hashlib
import html
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from extapi.google_auth import (
    consume_oauth_state,
    create_session,
    delete_session,
    get_session,
    store_oauth_state,
)

router = APIRouter(prefix="/google/auth", tags=["google-auth"])

_SCOPES = " ".join(
    [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/calendar",
    ]
)

_CALLBACK_PATH = "/google/auth/callback"


def _redirect_uri(settings) -> str:
    host = settings.host
    if host in ("0.0.0.0", "::", ""):
        host = "127.0.0.1"
    return f"http://{host}:{settings.port}{_CALLBACK_PATH}"


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _error_page(title: str, detail: str) -> HTMLResponse:
    body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 560px; margin: 40px auto;">
<h1>{html.escape(title)}</h1>
<p>{html.escape(detail)}</p>
</body></html>"""
    return HTMLResponse(content=body, status_code=400)


def _success_page(session_id: str, user_email: str, expires_at: str) -> HTMLResponse:
    body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Google auth complete</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto;">
<h1>Signed in as {html.escape(user_email)}</h1>
<p>Copy this session id and send it on future requests as the <code>X-Google-Session-Id</code> header:</p>
<pre style="padding: 12px; background: #f4f4f4; border-radius: 6px; user-select: all; word-break: break-all;">{html.escape(session_id)}</pre>
<p style="color: #555;">Token expires at {html.escape(expires_at)}. The server will refresh automatically while the session exists.</p>
</body></html>"""
    return HTMLResponse(content=body)


@router.get("/login")
async def login(request: Request):
    settings = request.app.state.settings
    db = request.app.state.google_auth_db

    state = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    await store_oauth_state(db, state, verifier)

    params = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": _redirect_uri(settings),
            "response_type": "code",
            "scope": _SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    return JSONResponse(content={"auth_url": auth_url})


@router.get("/callback")
async def callback(request: Request):
    settings = request.app.state.settings
    db = request.app.state.google_auth_db

    params = request.query_params
    if error := params.get("error"):
        return _error_page("Google returned an error", error)

    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        return _error_page("Missing parameters", "Expected both 'code' and 'state'.")

    verifier = await consume_oauth_state(db, state)
    if verifier is None:
        return _error_page(
            "Invalid or expired state",
            "Start the flow again via GET /google/auth/login.",
        )

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": _redirect_uri(settings),
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
        )
    if token_resp.status_code != 200:
        return _error_page("Token exchange failed", token_resp.text)

    token_data = token_resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)

    expiry = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if userinfo_resp.status_code != 200:
        return _error_page("Userinfo fetch failed", userinfo_resp.text)

    user_email = userinfo_resp.json().get("email", "unknown")

    session_id = await create_session(
        db, user_email, access_token, refresh_token, expiry, _SCOPES
    )

    return _success_page(session_id, user_email, expiry)


@router.get("/session/{session_id}")
async def get_session_info(session_id: str, request: Request):
    db = request.app.state.google_auth_db
    session = await get_session(db, session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    return JSONResponse(
        content={
            "session_id": session["session_id"],
            "user_email": session["user_email"],
            "expires_at": session["token_expiry"],
            "scopes": session["scopes"],
            "created_at": session["created_at"],
        }
    )


@router.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str, request: Request):
    db = request.app.state.google_auth_db
    deleted = await delete_session(db, session_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    return JSONResponse(content={"deleted": True})
