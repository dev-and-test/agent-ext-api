import httpx
import structlog

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "jira_mutation",
        service="jira",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def create_issue(
    client: httpx.AsyncClient, body: dict, caller_ip: str | None = None
) -> httpx.Response:
    path = "/rest/api/3/issue"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def get_issue(
    client: httpx.AsyncClient,
    issue_key: str,
    params: dict | None = None,
) -> httpx.Response:
    return await client.get(f"/rest/api/3/issue/{issue_key}", params=params)


async def update_issue(
    client: httpx.AsyncClient,
    issue_key: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/rest/api/3/issue/{issue_key}"
    resp = await client.put(path, json=body)
    await _log_mutation("PUT", path, resp, caller_ip)
    return resp


async def delete_issue(
    client: httpx.AsyncClient,
    issue_key: str,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/rest/api/3/issue/{issue_key}"
    resp = await client.delete(path)
    await _log_mutation("DELETE", path, resp, caller_ip)
    return resp


async def get_changelog(
    client: httpx.AsyncClient, issue_key: str
) -> httpx.Response:
    return await client.get(f"/rest/api/3/issue/{issue_key}/changelog")


async def search(
    client: httpx.AsyncClient, body: dict, caller_ip: str | None = None
) -> httpx.Response:
    path = "/rest/api/3/search"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def get_comments(
    client: httpx.AsyncClient, issue_key: str
) -> httpx.Response:
    return await client.get(f"/rest/api/3/issue/{issue_key}/comment")


async def create_comment(
    client: httpx.AsyncClient,
    issue_key: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/rest/api/3/issue/{issue_key}/comment"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def update_comment(
    client: httpx.AsyncClient,
    issue_key: str,
    comment_id: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/rest/api/3/issue/{issue_key}/comment/{comment_id}"
    resp = await client.put(path, json=body)
    await _log_mutation("PUT", path, resp, caller_ip)
    return resp


async def delete_comment(
    client: httpx.AsyncClient,
    issue_key: str,
    comment_id: str,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/rest/api/3/issue/{issue_key}/comment/{comment_id}"
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
