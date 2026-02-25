from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.gate import gate, gate_passthrough
from extapi.models.passthrough import PassthroughRequest
from extapi.services import gcalendar as gcalendar_svc

router = APIRouter(prefix="/gcalendar", tags=["gcalendar"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.get("/calendars")
async def list_calendars(request: Request):
    client = request.app.state.gcalendar_client
    params = {}
    for key in ("maxResults", "pageToken"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gcalendar_svc.list_calendars(client, params or None)
    return _forward(upstream)


@router.get("/calendars/{calendar_id}/events")
async def list_events(calendar_id: str, request: Request):
    client = request.app.state.gcalendar_client
    params = {}
    for key in ("q", "timeMin", "timeMax", "maxResults", "pageToken", "singleEvents", "orderBy"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gcalendar_svc.list_events(client, calendar_id, params or None)
    return _forward(upstream)


@router.get("/events/{calendar_id}/{event_id}")
async def get_event(calendar_id: str, event_id: str, request: Request):
    client = request.app.state.gcalendar_client
    upstream = await gcalendar_svc.get_event(client, calendar_id, event_id)
    return _forward(upstream)


@router.post("/calendars/{calendar_id}/events")
@gate("gcalendar", "POST", "/calendar/v3/calendars/{calendar_id}/events")
async def create_event(calendar_id: str, request: Request):
    body = await request.json()
    client = request.app.state.gcalendar_client
    caller_ip = request.client.host if request.client else None
    upstream = await gcalendar_svc.create_event(client, calendar_id, body, caller_ip)
    return _forward(upstream)


@router.patch("/events/{calendar_id}/{event_id}")
@gate("gcalendar", "PATCH", "/calendar/v3/calendars/{calendar_id}/events/{event_id}")
async def update_event(calendar_id: str, event_id: str, request: Request):
    body = await request.json()
    client = request.app.state.gcalendar_client
    caller_ip = request.client.host if request.client else None
    upstream = await gcalendar_svc.update_event(
        client, calendar_id, event_id, body, caller_ip
    )
    return _forward(upstream)


@router.delete("/events/{calendar_id}/{event_id}")
@gate("gcalendar", "DELETE", "/calendar/v3/calendars/{calendar_id}/events/{event_id}")
async def delete_event(calendar_id: str, event_id: str, request: Request):
    client = request.app.state.gcalendar_client
    caller_ip = request.client.host if request.client else None
    upstream = await gcalendar_svc.delete_event(
        client, calendar_id, event_id, caller_ip
    )
    return _forward(upstream)


@router.post("/passthrough")
@gate_passthrough("gcalendar")
async def gcalendar_passthrough(payload: PassthroughRequest, request: Request):
    client = request.app.state.gcalendar_client
    caller_ip = request.client.host if request.client else None
    upstream = await gcalendar_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
