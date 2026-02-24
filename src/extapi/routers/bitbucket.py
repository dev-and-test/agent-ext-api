from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.dry_run import maybe_block_delete
from extapi.models.passthrough import PassthroughRequest
from extapi.services import bitbucket as bb_svc

router = APIRouter(prefix="/bitbucket", tags=["bitbucket"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.get("/repos/{workspace}")
async def list_repos(workspace: str, request: Request):
    client = request.app.state.bitbucket_client
    upstream = await bb_svc.list_repos(client, workspace)
    return _forward(upstream)


@router.get("/repos/{workspace}/{repo_slug}")
async def get_repo(workspace: str, repo_slug: str, request: Request):
    client = request.app.state.bitbucket_client
    upstream = await bb_svc.get_repo(client, workspace, repo_slug)
    return _forward(upstream)


@router.get("/repos/{workspace}/{repo_slug}/branches")
async def list_branches(workspace: str, repo_slug: str, request: Request):
    client = request.app.state.bitbucket_client
    upstream = await bb_svc.list_branches(client, workspace, repo_slug)
    return _forward(upstream)


@router.get("/repos/{workspace}/{repo_slug}/pullrequests")
async def list_pullrequests(workspace: str, repo_slug: str, request: Request):
    client = request.app.state.bitbucket_client
    upstream = await bb_svc.list_pullrequests(client, workspace, repo_slug)
    return _forward(upstream)


@router.post("/repos/{workspace}/{repo_slug}/pullrequests")
async def create_pullrequest(workspace: str, repo_slug: str, request: Request):
    body = await request.json()
    client = request.app.state.bitbucket_client
    caller_ip = request.client.host if request.client else None
    upstream = await bb_svc.create_pullrequest(
        client, workspace, repo_slug, body, caller_ip
    )
    return _forward(upstream)


@router.get("/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}")
async def get_pullrequest(
    workspace: str, repo_slug: str, pr_id: int, request: Request
):
    client = request.app.state.bitbucket_client
    upstream = await bb_svc.get_pullrequest(client, workspace, repo_slug, pr_id)
    return _forward(upstream)


@router.put("/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}")
async def update_pullrequest(
    workspace: str, repo_slug: str, pr_id: int, request: Request
):
    body = await request.json()
    client = request.app.state.bitbucket_client
    caller_ip = request.client.host if request.client else None
    upstream = await bb_svc.update_pullrequest(
        client, workspace, repo_slug, pr_id, body, caller_ip
    )
    return _forward(upstream)


@router.post("/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge")
async def merge_pullrequest(
    workspace: str, repo_slug: str, pr_id: int, request: Request
):
    body = await request.json() if await request.body() else None
    client = request.app.state.bitbucket_client
    caller_ip = request.client.host if request.client else None
    upstream = await bb_svc.merge_pullrequest(
        client, workspace, repo_slug, pr_id, body, caller_ip
    )
    return _forward(upstream)


@router.post("/passthrough")
async def bitbucket_passthrough(payload: PassthroughRequest, request: Request):
    if payload.method == "DELETE":
        blocked = await maybe_block_delete(request, "bitbucket", payload.path)
        if blocked:
            return blocked
    client = request.app.state.bitbucket_client
    caller_ip = request.client.host if request.client else None
    upstream = await bb_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
