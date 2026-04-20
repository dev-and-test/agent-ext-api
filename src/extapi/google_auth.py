from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import aiosqlite
import httpx
import structlog

logger = structlog.get_logger()

_CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS google_sessions (
    session_id    TEXT PRIMARY KEY,
    user_email    TEXT NOT NULL,
    access_token  TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expiry  TEXT NOT NULL,
    scopes        TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""

_CREATE_STATES_TABLE = """
CREATE TABLE IF NOT EXISTS google_oauth_states (
    state         TEXT PRIMARY KEY,
    code_verifier TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
"""

_OAUTH_STATE_TTL = timedelta(minutes=10)


async def init_google_auth_db(path: str) -> aiosqlite.Connection:
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute(_CREATE_SESSIONS_TABLE)
    await db.execute(_CREATE_STATES_TABLE)
    await db.commit()
    return db


async def store_oauth_state(
    db: aiosqlite.Connection, state: str, code_verifier: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO google_oauth_states (state, code_verifier, created_at) VALUES (?, ?, ?)",
        (state, code_verifier, now),
    )
    await db.commit()


async def consume_oauth_state(db: aiosqlite.Connection, state: str) -> str | None:
    """Look up and delete the stored code_verifier for a state. Single-use.

    Also prunes entries older than the TTL to keep the table bounded.
    """
    cutoff = (datetime.now(timezone.utc) - _OAUTH_STATE_TTL).isoformat()
    await db.execute(
        "DELETE FROM google_oauth_states WHERE created_at < ?", (cutoff,)
    )
    async with db.execute(
        "SELECT code_verifier FROM google_oauth_states WHERE state = ?", (state,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        await db.commit()
        return None
    await db.execute("DELETE FROM google_oauth_states WHERE state = ?", (state,))
    await db.commit()
    return row["code_verifier"]


async def create_session(
    db: aiosqlite.Connection,
    email: str,
    access_token: str,
    refresh_token: str,
    expiry: str,
    scopes: str,
) -> str:
    session_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO google_sessions
           (session_id, user_email, access_token, refresh_token, token_expiry, scopes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, email, access_token, refresh_token, expiry, scopes, now, now),
    )
    await db.commit()
    return session_id


async def get_session(db: aiosqlite.Connection, session_id: str) -> dict | None:
    async with db.execute(
        "SELECT * FROM google_sessions WHERE session_id = ?", (session_id,)
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def delete_session(db: aiosqlite.Connection, session_id: str) -> bool:
    cur = await db.execute(
        "DELETE FROM google_sessions WHERE session_id = ?", (session_id,)
    )
    await db.commit()
    return cur.rowcount > 0


async def refresh_token_if_needed(
    db: aiosqlite.Connection,
    session: dict,
    client_id: str,
    client_secret: str,
) -> dict:
    expiry = datetime.fromisoformat(session["token_expiry"])
    if expiry - datetime.now(timezone.utc) > timedelta(minutes=5):
        return session

    await logger.ainfo(
        "refreshing_google_token",
        session_id=session["session_id"],
        user_email=session["user_email"],
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": session["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
    resp.raise_for_status()
    data = resp.json()

    new_access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    new_expiry = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        """UPDATE google_sessions
           SET access_token = ?, token_expiry = ?, updated_at = ?
           WHERE session_id = ?""",
        (new_access_token, new_expiry, now, session["session_id"]),
    )
    await db.commit()

    session = dict(session)
    session["access_token"] = new_access_token
    session["token_expiry"] = new_expiry
    session["updated_at"] = now
    return session
