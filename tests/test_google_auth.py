from urllib.parse import parse_qs, urlparse

import pytest

from extapi.main import app

TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _auth_url_params(auth_url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(auth_url).query).items()}


@pytest.mark.asyncio
async def test_login_returns_auth_url_with_pkce_and_loopback_redirect(client):
    c, _ = client
    resp = await c.get("/google/auth/login")
    assert resp.status_code == 200
    auth_url = resp.json()["auth_url"]
    assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")

    params = _auth_url_params(auth_url)
    assert params["response_type"] == "code"
    assert params["access_type"] == "offline"
    assert params["prompt"] == "consent"
    assert params["code_challenge_method"] == "S256"
    assert params["redirect_uri"] == "http://127.0.0.1:11583/google/auth/callback"
    assert len(params["state"]) >= 16
    assert len(params["code_challenge"]) >= 32
    assert "gmail.modify" in params["scope"]
    assert "drive" in params["scope"]
    assert "calendar" in params["scope"]


@pytest.mark.asyncio
async def test_callback_exchanges_code_and_creates_session(client):
    c, mock = client

    login_resp = await c.get("/google/auth/login")
    state = _auth_url_params(login_resp.json()["auth_url"])["state"]

    mock.post(TOKEN_URL).respond(
        200,
        json={
            "access_token": "ya29.fake",
            "refresh_token": "1//fake-refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )
    mock.get(USERINFO_URL).respond(200, json={"email": "user@example.com"})

    resp = await c.get(
        "/google/auth/callback",
        params={"code": "auth-code-123", "state": state},
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]

    # Token exchange must include PKCE verifier and the loopback redirect_uri
    token_call = next(c for c in mock.calls if c.request.url.path.endswith("/token"))
    body = dict(
        kv.split("=", 1) for kv in token_call.request.content.decode().split("&")
    )
    assert body["grant_type"] == "authorization_code"
    assert body["code"] == "auth-code-123"
    assert "code_verifier" in body and body["code_verifier"]
    assert body["redirect_uri"].startswith("http%3A%2F%2F127.0.0.1%3A11583")

    # Success HTML contains the session id — pull it out and verify the session exists
    db = app.state.google_auth_db
    async with db.execute(
        "SELECT session_id, user_email, refresh_token FROM google_sessions"
    ) as cur:
        row = await cur.fetchone()
    assert row is not None
    assert row["user_email"] == "user@example.com"
    assert row["refresh_token"] == "1//fake-refresh"
    assert row["session_id"] in resp.text

    # State must be single-use — row should be gone from google_oauth_states
    async with db.execute(
        "SELECT 1 FROM google_oauth_states WHERE state = ?", (state,)
    ) as cur:
        assert await cur.fetchone() is None


@pytest.mark.asyncio
async def test_get_session_info_returns_metadata_without_tokens(client):
    c, mock = client

    login_resp = await c.get("/google/auth/login")
    state = _auth_url_params(login_resp.json()["auth_url"])["state"]

    mock.post(TOKEN_URL).respond(
        200,
        json={
            "access_token": "ya29.fake",
            "refresh_token": "1//fake-refresh",
            "expires_in": 3600,
        },
    )
    mock.get(USERINFO_URL).respond(200, json={"email": "user@example.com"})

    callback_resp = await c.get(
        "/google/auth/callback", params={"code": "c", "state": state}
    )
    db = app.state.google_auth_db
    async with db.execute("SELECT session_id FROM google_sessions") as cur:
        session_id = (await cur.fetchone())["session_id"]
    assert session_id in callback_resp.text

    resp = await c.get(f"/google/auth/session/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["user_email"] == "user@example.com"
    assert "expires_at" in data
    assert "scopes" in data
    assert "access_token" not in data
    assert "refresh_token" not in data


@pytest.mark.asyncio
async def test_delete_session(client):
    c, mock = client

    login_resp = await c.get("/google/auth/login")
    state = _auth_url_params(login_resp.json()["auth_url"])["state"]
    mock.post(TOKEN_URL).respond(
        200, json={"access_token": "t", "refresh_token": "r", "expires_in": 3600}
    )
    mock.get(USERINFO_URL).respond(200, json={"email": "user@example.com"})
    await c.get("/google/auth/callback", params={"code": "c", "state": state})

    db = app.state.google_auth_db
    async with db.execute("SELECT session_id FROM google_sessions") as cur:
        session_id = (await cur.fetchone())["session_id"]

    resp = await c.delete(f"/google/auth/session/{session_id}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    follow_up = await c.get(f"/google/auth/session/{session_id}")
    assert follow_up.status_code == 404
