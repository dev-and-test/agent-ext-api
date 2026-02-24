import httpx
import structlog

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "gmail_mutation",
        service="gmail",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def search_messages(
    client: httpx.AsyncClient, params: dict | None = None
) -> httpx.Response:
    return await client.get("/gmail/v1/users/me/messages", params=params)


async def get_message(
    client: httpx.AsyncClient, message_id: str, params: dict | None = None
) -> httpx.Response:
    return await client.get(f"/gmail/v1/users/me/messages/{message_id}", params=params)


async def get_attachment(
    client: httpx.AsyncClient, message_id: str, attachment_id: str
) -> httpx.Response:
    return await client.get(
        f"/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"
    )


async def create_draft(
    client: httpx.AsyncClient, body: dict, caller_ip: str | None = None
) -> httpx.Response:
    path = "/gmail/v1/users/me/drafts"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
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
