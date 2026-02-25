import pytest

from extapi.main import app

JIRA = "https://yourco.atlassian.net"
SLACK = "https://slack.com/api"
GCAL = "https://www.googleapis.com"


def _set_approval(service: str, methods: str) -> None:
    """Set a service's approval gate and rebuild the lookup table."""
    setattr(app.state.settings, f"require_approval_{service}", methods)
    app.state.settings._build_approval_gates()


@pytest.fixture
def enable_jira_approval(client):
    """Require approval for all Jira mutations."""
    c, mock = client
    _set_approval("jira", "post,put,delete")
    yield c, mock
    _set_approval("jira", "")


@pytest.fixture
def enable_gmail_delete_approval(client):
    """Require approval for Gmail deletes only."""
    c, mock = client
    _set_approval("gmail", "delete")
    yield c, mock
    _set_approval("gmail", "")


@pytest.fixture
def enable_gcalendar_approval(client):
    c, mock = client
    _set_approval("gcalendar", "post,patch,delete")
    yield c, mock
    _set_approval("gcalendar", "")


# --- Enqueue tests ---


@pytest.mark.asyncio
async def test_jira_create_issue_enqueued(enable_jira_approval):
    c, mock = enable_jira_approval
    resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    assert resp.status_code == 202
    body = resp.json()
    assert body["queued"] is True
    assert body["service"] == "jira"
    assert "review_id" in body


@pytest.mark.asyncio
async def test_jira_update_issue_enqueued(enable_jira_approval):
    c, mock = enable_jira_approval
    resp = await c.put("/jira/issues/PROJ-1", json={"fields": {"summary": "updated"}})
    assert resp.status_code == 202
    body = resp.json()
    assert body["queued"] is True
    assert body["service"] == "jira"


@pytest.mark.asyncio
async def test_jira_delete_issue_enqueued(enable_jira_approval):
    c, mock = enable_jira_approval
    resp = await c.delete("/jira/issues/PROJ-1")
    assert resp.status_code == 202
    body = resp.json()
    assert body["queued"] is True


@pytest.mark.asyncio
async def test_jira_passthrough_post_enqueued(enable_jira_approval):
    c, mock = enable_jira_approval
    resp = await c.post(
        "/jira/passthrough",
        json={"method": "POST", "path": "/rest/api/3/issue", "body": {"fields": {}}},
    )
    assert resp.status_code == 202
    assert resp.json()["queued"] is True


@pytest.mark.asyncio
async def test_jira_passthrough_get_not_enqueued(enable_jira_approval):
    """GET requests are never enqueued."""
    c, mock = enable_jira_approval
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(200, json={"key": "PROJ-1"})
    resp = await c.post(
        "/jira/passthrough",
        json={"method": "GET", "path": "/rest/api/3/issue/PROJ-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_slack_not_enqueued_when_not_configured(client):
    """Slack messages go through when no approval required."""
    c, mock = client
    mock.post(f"{SLACK}/chat.postMessage").respond(200, json={"ok": True})
    resp = await c.post("/slack/messages", json={"channel": "C1", "text": "hi"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_gmail_passthrough_delete_enqueued(enable_gmail_delete_approval):
    """Gmail DELETE via passthrough is enqueued when only delete approval is on."""
    c, mock = enable_gmail_delete_approval
    resp = await c.post(
        "/gmail/passthrough",
        json={"method": "DELETE", "path": "/gmail/v1/users/me/messages/msg1"},
    )
    assert resp.status_code == 202
    assert resp.json()["queued"] is True


@pytest.mark.asyncio
async def test_gmail_post_not_enqueued_when_only_delete_configured(enable_gmail_delete_approval):
    """Gmail POST goes through when only delete approval is configured."""
    c, mock = enable_gmail_delete_approval
    mock.post("https://gmail.googleapis.com/gmail/v1/users/me/drafts").respond(
        200, json={"id": "draft1"}
    )
    resp = await c.post("/gmail/drafts", json={"message": {"raw": "abc"}})
    assert resp.status_code == 200


# --- Review CRUD tests ---


@pytest.mark.asyncio
async def test_list_queue_empty(client):
    c, mock = client
    resp = await c.get("/review/queue")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_list_queue_with_items(enable_jira_approval):
    c, mock = enable_jira_approval
    # Enqueue two items
    await c.post("/jira/issues", json={"fields": {"summary": "one"}})
    await c.put("/jira/issues/PROJ-1", json={"fields": {"summary": "two"}})

    resp = await c.get("/review/queue")
    assert resp.json()["count"] == 2


@pytest.mark.asyncio
async def test_list_queue_filter_by_status(enable_jira_approval):
    c, mock = enable_jira_approval
    await c.post("/jira/issues", json={"fields": {"summary": "one"}})
    resp = await c.get("/review/queue?status=pending")
    assert resp.json()["count"] == 1
    resp = await c.get("/review/queue?status=approved")
    assert resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_list_queue_filter_by_service(enable_jira_approval, enable_gcalendar_approval):
    c, mock = enable_jira_approval
    await c.post("/jira/issues", json={"fields": {"summary": "jira item"}})
    await c.post(
        "/gcalendar/calendars/primary/events",
        json={"summary": "calendar event"},
    )
    resp = await c.get("/review/queue?service=jira")
    assert resp.json()["count"] == 1
    assert resp.json()["items"][0]["service"] == "jira"


@pytest.mark.asyncio
async def test_get_queue_item(enable_jira_approval):
    c, mock = enable_jira_approval
    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    resp = await c.get(f"/review/queue/{review_id}")
    assert resp.status_code == 200
    item = resp.json()
    assert item["id"] == review_id
    assert item["status"] == "pending"
    assert item["service"] == "jira"
    assert item["method"] == "POST"
    assert item["body"] == {"fields": {"summary": "test"}}


@pytest.mark.asyncio
async def test_get_queue_item_not_found(client):
    c, mock = client
    resp = await c.get("/review/queue/nonexistent")
    assert resp.status_code == 404


# --- Approve tests ---


@pytest.mark.asyncio
async def test_approve_executes_upstream(enable_jira_approval):
    c, mock = enable_jira_approval
    mock.post(f"{JIRA}/rest/api/3/issue").respond(
        201, json={"id": "10001", "key": "PROJ-42"}
    )

    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    approve_resp = await c.post(f"/review/queue/{review_id}/approve")
    assert approve_resp.status_code == 200
    item = approve_resp.json()
    assert item["status"] == "approved"
    assert item["response_status"] == 201
    assert item["decided_at"] is not None


@pytest.mark.asyncio
async def test_approve_already_approved(enable_jira_approval):
    c, mock = enable_jira_approval
    mock.post(f"{JIRA}/rest/api/3/issue").respond(201, json={"key": "PROJ-1"})

    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    await c.post(f"/review/queue/{review_id}/approve")
    resp = await c.post(f"/review/queue/{review_id}/approve")
    assert resp.status_code == 409
    assert resp.json()["error"] == "not_pending"


@pytest.mark.asyncio
async def test_approve_not_found(client):
    c, mock = client
    resp = await c.post("/review/queue/nonexistent/approve")
    assert resp.status_code == 404


# --- Reject tests ---


@pytest.mark.asyncio
async def test_reject_item(enable_jira_approval):
    c, mock = enable_jira_approval
    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    reject_resp = await c.post(f"/review/queue/{review_id}/reject")
    assert reject_resp.status_code == 200
    item = reject_resp.json()
    assert item["status"] == "rejected"
    assert item["decided_at"] is not None


@pytest.mark.asyncio
async def test_reject_already_rejected(enable_jira_approval):
    c, mock = enable_jira_approval
    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    await c.post(f"/review/queue/{review_id}/reject")
    resp = await c.post(f"/review/queue/{review_id}/reject")
    assert resp.status_code == 409


# --- Delete tests ---


@pytest.mark.asyncio
async def test_delete_queue_item(enable_jira_approval):
    c, mock = enable_jira_approval
    create_resp = await c.post("/jira/issues", json={"fields": {"summary": "test"}})
    review_id = create_resp.json()["review_id"]

    del_resp = await c.delete(f"/review/queue/{review_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # Verify it's gone
    get_resp = await c.get(f"/review/queue/{review_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found(client):
    c, mock = client
    resp = await c.delete("/review/queue/nonexistent")
    assert resp.status_code == 404


# --- Dry-run still works alongside approval ---


@pytest.mark.asyncio
async def test_dry_run_takes_precedence_over_approval(client):
    """dry_run_deletes blocks immediately, before approval queue check."""
    c, mock = client
    app.state.settings.dry_run_deletes = True
    _set_approval("jira", "delete")
    try:
        resp = await c.delete("/jira/issues/PROJ-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["dry_run"] is True
        # Nothing should be in the queue
        queue_resp = await c.get("/review/queue")
        assert queue_resp.json()["count"] == 0
    finally:
        app.state.settings.dry_run_deletes = False
        _set_approval("jira", "")


# --- GCalendar approval tests ---


@pytest.mark.asyncio
async def test_gcalendar_create_event_enqueued(enable_gcalendar_approval):
    c, mock = enable_gcalendar_approval
    resp = await c.post(
        "/gcalendar/calendars/primary/events",
        json={"summary": "meeting"},
    )
    assert resp.status_code == 202
    assert resp.json()["queued"] is True
    assert resp.json()["service"] == "gcalendar"


@pytest.mark.asyncio
async def test_gcalendar_delete_event_enqueued(enable_gcalendar_approval):
    c, mock = enable_gcalendar_approval
    resp = await c.delete("/gcalendar/events/primary/evt1")
    assert resp.status_code == 202
    assert resp.json()["queued"] is True


@pytest.mark.asyncio
async def test_gcalendar_approve_event_creation(enable_gcalendar_approval):
    c, mock = enable_gcalendar_approval
    mock.post(f"{GCAL}/calendar/v3/calendars/primary/events").respond(
        200, json={"id": "evt99"}
    )

    create_resp = await c.post(
        "/gcalendar/calendars/primary/events",
        json={"summary": "meeting"},
    )
    review_id = create_resp.json()["review_id"]

    approve_resp = await c.post(f"/review/queue/{review_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    assert approve_resp.json()["response_status"] == 200
