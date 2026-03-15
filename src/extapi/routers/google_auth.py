from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from extapi.google_auth import create_session, delete_session, get_session

router = APIRouter(prefix="/google/auth", tags=["google-auth"])

_SCOPES = " ".join(
    [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/calendar",
    ]
)

_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


@router.get("/login")
async def login(request: Request):
    settings = request.app.state.settings
    params = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": _REDIRECT_URI,
            "response_type": "code",
            "scope": _SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    return JSONResponse(content={"auth_url": auth_url})


class CallbackRequest(BaseModel):
    code: str


@router.post("/callback")
async def callback(payload: CallbackRequest, request: Request):
    settings = request.app.state.settings

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": payload.code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": _REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if token_resp.status_code != 200:
        return JSONResponse(
            status_code=400,
            content={"error": "token_exchange_failed", "detail": token_resp.text},
        )

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
        return JSONResponse(
            status_code=400,
            content={"error": "userinfo_failed", "detail": userinfo_resp.text},
        )

    user_email = userinfo_resp.json().get("email", "unknown")

    db = request.app.state.google_auth_db
    session_id = await create_session(
        db, user_email, access_token, refresh_token, expiry, _SCOPES
    )

    return JSONResponse(
        content={
            "session_id": session_id,
            "user_email": user_email,
            "expires_at": expiry,
        }
    )


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
