import pytest

GMAIL = "https://gmail.googleapis.com"


@pytest.mark.asyncio
async def test_search_messages(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages").respond(
        200, json={"messages": [{"id": "msg1", "threadId": "t1"}], "resultSizeEstimate": 1}
    )
    resp = await c.get("/gmail/messages?q=is:unread")
    assert resp.status_code == 200
    assert resp.json()["messages"][0]["id"] == "msg1"


@pytest.mark.asyncio
async def test_search_messages_with_params(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages").respond(
        200, json={"messages": [], "resultSizeEstimate": 0}
    )
    resp = await c.get("/gmail/messages?q=from:test&maxResults=5&pageToken=abc")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_message(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages/msg123").respond(
        200, json={"id": "msg123", "snippet": "Hello world"}
    )
    resp = await c.get("/gmail/messages/msg123")
    assert resp.status_code == 200
    assert resp.json()["id"] == "msg123"


@pytest.mark.asyncio
async def test_get_message_with_format(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages/msg123").respond(
        200, json={"id": "msg123", "payload": {}}
    )
    resp = await c.get("/gmail/messages/msg123?format=full")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_attachment(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages/msg1/attachments/att1").respond(
        200, json={"attachmentId": "att1", "size": 1024, "data": "base64data"}
    )
    resp = await c.get("/gmail/messages/msg1/attachments/att1")
    assert resp.status_code == 200
    assert resp.json()["attachmentId"] == "att1"


@pytest.mark.asyncio
async def test_create_draft(client):
    c, mock = client
    mock.post(f"{GMAIL}/gmail/v1/users/me/drafts").respond(
        200, json={"id": "draft1", "message": {"id": "msg1"}}
    )
    resp = await c.post(
        "/gmail/drafts",
        json={"message": {"raw": "base64encoded"}},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == "draft1"


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/labels").respond(
        200, json={"labels": [{"id": "INBOX", "name": "INBOX"}]}
    )
    resp = await c.post(
        "/gmail/passthrough",
        json={"method": "GET", "path": "/gmail/v1/users/me/labels"},
    )
    assert resp.status_code == 200
    assert resp.json()["labels"][0]["id"] == "INBOX"


@pytest.mark.asyncio
async def test_passthrough_mutation(client):
    c, mock = client
    mock.post(f"{GMAIL}/gmail/v1/users/me/labels").respond(
        200, json={"id": "Label_1", "name": "Custom"}
    )
    resp = await c.post(
        "/gmail/passthrough",
        json={
            "method": "POST",
            "path": "/gmail/v1/users/me/labels",
            "body": {"name": "Custom"},
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.get(f"{GMAIL}/gmail/v1/users/me/messages/bad").respond(
        404, json={"error": {"code": 404, "message": "Not Found"}}
    )
    resp = await c.get("/gmail/messages/bad")
    assert resp.status_code == 404
