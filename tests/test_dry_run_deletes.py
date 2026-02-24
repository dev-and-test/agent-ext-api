import pytest


@pytest.fixture
def enable_dry_run(client):
    """Enable dry_run_deletes for the duration of the test."""
    c, mock = client
    from extapi.main import app

    app.state.settings.dry_run_deletes = True
    yield c, mock
    app.state.settings.dry_run_deletes = False


@pytest.mark.asyncio
async def test_jira_delete_issue_blocked(enable_dry_run):
    c, mock = enable_dry_run
    # No upstream mock needed — request should never reach upstream
    resp = await c.delete("/jira/issues/PROJ-123")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "jira"
    assert "PROJ-123" in body["path"]


@pytest.mark.asyncio
async def test_jira_delete_comment_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.delete("/jira/issues/PROJ-123/comments/456")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "jira"
    assert "456" in body["path"]


@pytest.mark.asyncio
async def test_jira_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/jira/passthrough",
        json={"method": "DELETE", "path": "/rest/api/3/issue/PROJ-999"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "jira"


@pytest.mark.asyncio
async def test_jira_passthrough_get_not_blocked(enable_dry_run):
    c, mock = enable_dry_run
    JIRA = "https://yourco.atlassian.net"
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(
        200, json={"key": "PROJ-1"}
    )
    resp = await c.post(
        "/jira/passthrough",
        json={"method": "GET", "path": "/rest/api/3/issue/PROJ-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_gcalendar_delete_event_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.delete("/gcalendar/events/primary/evt1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "gcalendar"
    assert "evt1" in body["path"]


@pytest.mark.asyncio
async def test_gcalendar_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/gcalendar/passthrough",
        json={"method": "DELETE", "path": "/calendar/v3/calendars/secondary"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "gcalendar"


@pytest.mark.asyncio
async def test_gdrive_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/gdrive/passthrough",
        json={"method": "DELETE", "path": "/drive/v3/files/file123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "gdrive"


@pytest.mark.asyncio
async def test_gmail_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/gmail/passthrough",
        json={"method": "DELETE", "path": "/gmail/v1/users/me/messages/msg1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "gmail"


@pytest.mark.asyncio
async def test_slack_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/slack/passthrough",
        json={"method": "DELETE", "path": "/chat.delete"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "slack"


@pytest.mark.asyncio
async def test_bitbucket_passthrough_delete_blocked(enable_dry_run):
    c, mock = enable_dry_run
    resp = await c.post(
        "/bitbucket/passthrough",
        json={"method": "DELETE", "path": "/repositories/ws/repo"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["service"] == "bitbucket"


@pytest.mark.asyncio
async def test_delete_works_when_flag_disabled(client):
    """When dry_run_deletes is False (default), deletes go through normally."""
    c, mock = client
    JIRA = "https://yourco.atlassian.net"
    mock.delete(f"{JIRA}/rest/api/3/issue/PROJ-123").respond(204)
    resp = await c.delete("/jira/issues/PROJ-123")
    assert resp.status_code == 204
