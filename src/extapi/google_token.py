from __future__ import annotations

import structlog
from fastapi import Request

from extapi.google_auth import get_session, refresh_token_if_needed

logger = structlog.get_logger()


def auth_headers(token: str | None) -> dict[str, str] | None:
    if token:
        return {"Authorization": f"Bearer {token}"}
    return None


async def get_google_token(request: Request) -> str | None:
    """Read X-Google-Session-Id header, look up session, refresh if needed, return access_token or None."""
    session_id = request.headers.get("X-Google-Session-Id")
    if not session_id:
        return None

    db = request.app.state.google_auth_db
    session = await get_session(db, session_id)
    if not session:
        await logger.awarn("google_session_not_found", session_id=session_id)
        return None

    settings = request.app.state.settings
    session = await refresh_token_if_needed(
        db,
        session,
        settings.google_oauth_client_id,
        settings.google_oauth_client_secret,
    )
    return session["access_token"]
