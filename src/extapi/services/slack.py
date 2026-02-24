import httpx
import structlog

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "slack_mutation",
        service="slack",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def post_message(
    client: httpx.AsyncClient, body: dict, caller_ip: str | None = None
) -> httpx.Response:
    path = "/chat.postMessage"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def get_history(
    client: httpx.AsyncClient, channel_id: str, params: dict | None = None
) -> httpx.Response:
    return await client.get("/conversations.history", params={"channel": channel_id, **(params or {})})


async def get_replies(
    client: httpx.AsyncClient, channel_id: str, ts: str, params: dict | None = None
) -> httpx.Response:
    return await client.get(
        "/conversations.replies",
        params={"channel": channel_id, "ts": ts, **(params or {})},
    )


async def list_channels(
    client: httpx.AsyncClient, params: dict | None = None
) -> httpx.Response:
    return await client.get("/conversations.list", params=params)


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
