from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.dry_run import maybe_block_delete
from extapi.models.passthrough import PassthroughRequest
from extapi.services import gmail as gmail_svc

router = APIRouter(prefix="/gmail", tags=["gmail"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.get("/messages")
async def search_messages(request: Request):
    client = request.app.state.gmail_client
    params = {}
    for key in ("q", "maxResults", "pageToken", "labelIds"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gmail_svc.search_messages(client, params or None)
    return _forward(upstream)


@router.get("/messages/{message_id}")
async def get_message(message_id: str, request: Request):
    client = request.app.state.gmail_client
    params = {}
    for key in ("format", "metadataHeaders"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gmail_svc.get_message(client, message_id, params or None)
    return _forward(upstream)


@router.get("/messages/{message_id}/attachments/{attachment_id}")
async def get_attachment(message_id: str, attachment_id: str, request: Request):
    client = request.app.state.gmail_client
    upstream = await gmail_svc.get_attachment(client, message_id, attachment_id)
    return _forward(upstream)


@router.post("/drafts")
async def create_draft(request: Request):
    body = await request.json()
    client = request.app.state.gmail_client
    caller_ip = request.client.host if request.client else None
    upstream = await gmail_svc.create_draft(client, body, caller_ip)
    return _forward(upstream)


@router.post("/passthrough")
async def gmail_passthrough(payload: PassthroughRequest, request: Request):
    if payload.method == "DELETE":
        blocked = await maybe_block_delete(request, "gmail", payload.path)
        if blocked:
            return blocked
    client = request.app.state.gmail_client
    caller_ip = request.client.host if request.client else None
    upstream = await gmail_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
