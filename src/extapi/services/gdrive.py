import httpx
import structlog

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "gdrive_mutation",
        service="gdrive",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def list_files(
    client: httpx.AsyncClient, params: dict | None = None
) -> httpx.Response:
    return await client.get("/drive/v3/files", params=params)


async def get_file(
    client: httpx.AsyncClient, file_id: str, params: dict | None = None
) -> httpx.Response:
    return await client.get(f"/drive/v3/files/{file_id}", params=params)


async def download_file(
    client: httpx.AsyncClient, file_id: str
) -> httpx.Response:
    return await client.get(f"/drive/v3/files/{file_id}", params={"alt": "media"})


async def create_file(
    client: httpx.AsyncClient, body: dict, caller_ip: str | None = None
) -> httpx.Response:
    path = "/drive/v3/files"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def update_file(
    client: httpx.AsyncClient,
    file_id: str,
    body: dict,
    params: dict | None = None,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/drive/v3/files/{file_id}"
    resp = await client.patch(path, json=body, params=params)
    await _log_mutation("PATCH", path, resp, caller_ip)
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
