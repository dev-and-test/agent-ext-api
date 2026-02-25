from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.gate import gate, gate_passthrough
from extapi.models.passthrough import PassthroughRequest
from extapi.services import jira as jira_svc

router = APIRouter(prefix="/jira", tags=["jira"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.post("/issues")
@gate("jira", "POST", "/rest/api/3/issue")
async def create_issue(request: Request):
    body = await request.json()
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.create_issue(client, body, caller_ip)
    return _forward(upstream)


@router.get("/issues/{issue_key}")
async def get_issue(issue_key: str, request: Request):
    client = request.app.state.jira_client
    params = {}
    for key in ("fields", "expand"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await jira_svc.get_issue(client, issue_key, params or None)
    return _forward(upstream)


@router.put("/issues/{issue_key}")
@gate("jira", "PUT", "/rest/api/3/issue/{issue_key}")
async def update_issue(issue_key: str, request: Request):
    body = await request.json()
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.update_issue(client, issue_key, body, caller_ip)
    return _forward(upstream)


@router.delete("/issues/{issue_key}")
@gate("jira", "DELETE", "/rest/api/3/issue/{issue_key}")
async def delete_issue(issue_key: str, request: Request):
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.delete_issue(client, issue_key, caller_ip)
    return _forward(upstream)


@router.get("/issues/{issue_key}/changelog")
async def get_changelog(issue_key: str, request: Request):
    client = request.app.state.jira_client
    upstream = await jira_svc.get_changelog(client, issue_key)
    return _forward(upstream)


@router.post("/search")
async def search(request: Request):
    body = await request.json()
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.search(client, body, caller_ip)
    return _forward(upstream)


@router.get("/issues/{issue_key}/comments")
async def get_comments(issue_key: str, request: Request):
    client = request.app.state.jira_client
    upstream = await jira_svc.get_comments(client, issue_key)
    return _forward(upstream)


@router.post("/issues/{issue_key}/comments")
@gate("jira", "POST", "/rest/api/3/issue/{issue_key}/comment")
async def create_comment(issue_key: str, request: Request):
    body = await request.json()
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.create_comment(client, issue_key, body, caller_ip)
    return _forward(upstream)


@router.put("/issues/{issue_key}/comments/{comment_id}")
@gate("jira", "PUT", "/rest/api/3/issue/{issue_key}/comment/{comment_id}")
async def update_comment(issue_key: str, comment_id: str, request: Request):
    body = await request.json()
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.update_comment(
        client, issue_key, comment_id, body, caller_ip
    )
    return _forward(upstream)


@router.delete("/issues/{issue_key}/comments/{comment_id}")
@gate("jira", "DELETE", "/rest/api/3/issue/{issue_key}/comment/{comment_id}")
async def delete_comment(issue_key: str, comment_id: str, request: Request):
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.delete_comment(client, issue_key, comment_id, caller_ip)
    return _forward(upstream)


@router.post("/passthrough")
@gate_passthrough("jira")
async def jira_passthrough(payload: PassthroughRequest, request: Request):
    client = request.app.state.jira_client
    caller_ip = request.client.host if request.client else None
    upstream = await jira_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
