import pytest

GCAL = "https://www.googleapis.com"


@pytest.mark.asyncio
async def test_list_calendars(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/users/me/calendarList").respond(
        200, json={"kind": "calendar#calendarList", "items": [{"id": "primary"}]}
    )
    resp = await c.get("/gcalendar/calendars")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == "primary"


@pytest.mark.asyncio
async def test_list_calendars_with_params(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/users/me/calendarList").respond(
        200, json={"items": []}
    )
    resp = await c.get("/gcalendar/calendars?maxResults=5&pageToken=abc")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_events(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/calendars/primary/events").respond(
        200, json={"items": [{"id": "evt1", "summary": "Meeting"}]}
    )
    resp = await c.get("/gcalendar/calendars/primary/events")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == "evt1"


@pytest.mark.asyncio
async def test_list_events_with_params(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/calendars/primary/events").respond(
        200, json={"items": []}
    )
    resp = await c.get(
        "/gcalendar/calendars/primary/events"
        "?timeMin=2026-02-24T00:00:00Z&timeMax=2026-02-25T00:00:00Z"
        "&singleEvents=true&orderBy=startTime&maxResults=10"
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_event(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/calendars/primary/events/evt1").respond(
        200, json={"id": "evt1", "summary": "Meeting", "status": "confirmed"}
    )
    resp = await c.get("/gcalendar/events/primary/evt1")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Meeting"


@pytest.mark.asyncio
async def test_create_event(client):
    c, mock = client
    mock.post(f"{GCAL}/calendar/v3/calendars/primary/events").respond(
        200, json={"id": "new_evt", "summary": "New Event"}
    )
    resp = await c.post(
        "/gcalendar/calendars/primary/events",
        json={
            "summary": "New Event",
            "start": {"dateTime": "2026-02-25T10:00:00Z"},
            "end": {"dateTime": "2026-02-25T11:00:00Z"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == "new_evt"


@pytest.mark.asyncio
async def test_update_event(client):
    c, mock = client
    mock.patch(f"{GCAL}/calendar/v3/calendars/primary/events/evt1").respond(
        200, json={"id": "evt1", "summary": "Updated Meeting"}
    )
    resp = await c.patch(
        "/gcalendar/events/primary/evt1",
        json={"summary": "Updated Meeting"},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Updated Meeting"


@pytest.mark.asyncio
async def test_delete_event(client):
    c, mock = client
    mock.delete(f"{GCAL}/calendar/v3/calendars/primary/events/evt1").respond(204)
    resp = await c.delete("/gcalendar/events/primary/evt1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/colors").respond(
        200, json={"kind": "calendar#colors"}
    )
    resp = await c.post(
        "/gcalendar/passthrough",
        json={"method": "GET", "path": "/calendar/v3/colors"},
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "calendar#colors"


@pytest.mark.asyncio
async def test_passthrough_mutation(client):
    c, mock = client
    mock.delete(f"{GCAL}/calendar/v3/calendars/secondary").respond(204)
    resp = await c.post(
        "/gcalendar/passthrough",
        json={"method": "DELETE", "path": "/calendar/v3/calendars/secondary"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.get(f"{GCAL}/calendar/v3/calendars/bad/events/nope").respond(
        404, json={"error": {"code": 404, "message": "Not Found"}}
    )
    resp = await c.get("/gcalendar/events/bad/nope")
    assert resp.status_code == 404
