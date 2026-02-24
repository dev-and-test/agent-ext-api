import pytest

SLACK = "https://slack.com/api"


@pytest.mark.asyncio
async def test_post_message(client):
    c, mock = client
    mock.post(f"{SLACK}/chat.postMessage").respond(
        200, json={"ok": True, "channel": "C123", "ts": "1234567890.123456"}
    )
    resp = await c.post(
        "/slack/messages", json={"channel": "C123", "text": "Hello"}
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_get_history(client):
    c, mock = client
    mock.get(f"{SLACK}/conversations.history").respond(
        200, json={"ok": True, "messages": []}
    )
    resp = await c.get("/slack/channels/C123/history")
    assert resp.status_code == 200
    assert resp.json()["messages"] == []


@pytest.mark.asyncio
async def test_get_history_with_params(client):
    c, mock = client
    mock.get(f"{SLACK}/conversations.history").respond(
        200, json={"ok": True, "messages": []}
    )
    resp = await c.get("/slack/channels/C123/history?limit=10&oldest=0")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_replies(client):
    c, mock = client
    mock.get(f"{SLACK}/conversations.replies").respond(
        200, json={"ok": True, "messages": []}
    )
    resp = await c.get("/slack/channels/C123/replies?ts=1234567890.123456")
    assert resp.status_code == 200
    assert resp.json()["messages"] == []


@pytest.mark.asyncio
async def test_get_replies_requires_ts(client):
    c, _ = client
    resp = await c.get("/slack/channels/C123/replies")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_channels(client):
    c, mock = client
    mock.get(f"{SLACK}/conversations.list").respond(
        200, json={"ok": True, "channels": [{"id": "C123", "name": "general"}]}
    )
    resp = await c.get("/slack/channels")
    assert resp.status_code == 200
    assert resp.json()["channels"][0]["id"] == "C123"


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{SLACK}/auth.test").respond(200, json={"ok": True, "user": "bot"})
    resp = await c.post(
        "/slack/passthrough",
        json={"method": "GET", "path": "/auth.test"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_passthrough_mutation(client):
    c, mock = client
    mock.post(f"{SLACK}/chat.update").respond(200, json={"ok": True})
    resp = await c.post(
        "/slack/passthrough",
        json={
            "method": "POST",
            "path": "/chat.update",
            "body": {"channel": "C123", "ts": "123", "text": "updated"},
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.post(f"{SLACK}/chat.postMessage").respond(
        200, json={"ok": False, "error": "channel_not_found"}
    )
    resp = await c.post(
        "/slack/messages", json={"channel": "BAD", "text": "Hello"}
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is False
