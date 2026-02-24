import httpx
import structlog

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
    client: httpx.AsyncClient, params: dict | None = None
) -> httpx.Response:
    return await client.get("/calendar/v3/users/me/calendarList", params=params)


async def list_events(
    client: httpx.AsyncClient, calendar_id: str, params: dict | None = None
) -> httpx.Response:
    return await client.get(
        f"/calendar/v3/calendars/{calendar_id}/events", params=params
    )


async def get_event(
    client: httpx.AsyncClient, calendar_id: str, event_id: str
) -> httpx.Response:
    return await client.get(
        f"/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    )


async def create_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def update_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    event_id: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    resp = await client.patch(path, json=body)
    await _log_mutation("PATCH", path, resp, caller_ip)
    return resp


async def delete_event(
    client: httpx.AsyncClient,
    calendar_id: str,
    event_id: str,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/calendar/v3/calendars/{calendar_id}/events/{event_id}"
    resp = await client.delete(path)
    await _log_mutation("DELETE", path, resp, caller_ip)
    return resp


async def passthrough(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    body: dict | None = None,
    params: dict[str, str] | None = None,
    caller_ip: str | None = None,
) -> httpx.Response:
    resp = await client.request(method, path, json=body, params=params)
    if method != "GET":
        await _log_mutation(method, path, resp, caller_ip)
    return resp
