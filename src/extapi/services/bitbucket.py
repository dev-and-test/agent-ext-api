import httpx
import structlog

logger = structlog.get_logger()


async def _log_mutation(
    method: str, path: str, response: httpx.Response, caller_ip: str | None
) -> None:
    await logger.ainfo(
        "bitbucket_mutation",
        service="bitbucket",
        method=method,
        upstream_path=path,
        status_code=response.status_code,
        caller_ip=caller_ip,
    )


async def list_repos(
    client: httpx.AsyncClient, workspace: str, params: dict | None = None
) -> httpx.Response:
    return await client.get(f"/repositories/{workspace}", params=params)


async def get_repo(
    client: httpx.AsyncClient, workspace: str, repo_slug: str
) -> httpx.Response:
    return await client.get(f"/repositories/{workspace}/{repo_slug}")


async def list_branches(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    params: dict | None = None,
) -> httpx.Response:
    return await client.get(
        f"/repositories/{workspace}/{repo_slug}/refs/branches",
        params=params,
    )


async def list_pullrequests(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    params: dict | None = None,
) -> httpx.Response:
    return await client.get(
        f"/repositories/{workspace}/{repo_slug}/pullrequests",
        params=params,
    )


async def create_pullrequest(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/repositories/{workspace}/{repo_slug}/pullrequests"
    resp = await client.post(path, json=body)
    await _log_mutation("POST", path, resp, caller_ip)
    return resp


async def get_pullrequest(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    pr_id: int,
) -> httpx.Response:
    return await client.get(
        f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"
    )


async def update_pullrequest(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    pr_id: int,
    body: dict,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"
    resp = await client.put(path, json=body)
    await _log_mutation("PUT", path, resp, caller_ip)
    return resp


async def merge_pullrequest(
    client: httpx.AsyncClient,
    workspace: str,
    repo_slug: str,
    pr_id: int,
    body: dict | None = None,
    caller_ip: str | None = None,
) -> httpx.Response:
    path = f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge"
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
