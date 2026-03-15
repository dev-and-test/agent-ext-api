import httpx
import structlog

from extapi.google_token import auth_headers

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "gcalendar_mutation",
        service="gcalendar",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def list_calendars(
    client: httpx.AsyncClient, params: dict | None = None, token: str | None = None
) -> httpx.Response:
    return await client.get("/calendar/v3/users/me/calendarList", params=params, headers=auth_headers(token))


async def list_events(
    client: httpx.AsyncClient, calendar_id: str, params: dict | None = None, token: str | None = None
) -> httpx.Response:
    return await client.get(
        f"/calendar/v3/calendars/{calendar_id}/events", params=params, headers=auth_headers(token)
    )


async def get_event(
    client: httpx.AsyncClient, calendar_id: str, event_id: str, token: str | None = None
) -> httpx.Response:
    return await client.get(
        f"/calendar/v3/calendars/{calendar_id}/events/{event_id}", headers=auth_headers(token)
    )


async def create_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    body: dict,
    caller_ip: str | None = None,
    token: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events"
    resp = await client.post(path, json=body, headers=auth_headers(token))
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def update_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    event_id: str,
    body: dict,
    caller_ip: str | None = None,
    token: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    resp = await client.patch(path, json=body, headers=auth_headers(token))
    await _log_mutation("PATCH", path, resp, caller_ip)
    return resp


async def delete_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    event_id: str,
    caller_ip: str | None = None,
    token: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    resp = await client.delete(path, headers=auth_headers(token))
    await _log_mutation("DELETE", path, resp, caller_ip)
    return resp


async def passthrough(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    body: dict | None = None,
    params: dict[str, str] | None = None,
    caller_ip: str | None = None,
    token: str | None = None,
) -> httpx.Response:
    resp = await client.request(method, path, json=body, params=params, headers=auth_headers(token))
    if method != "GET":
        await _log_mutation(method, path, resp, caller_ip)
    return resp
