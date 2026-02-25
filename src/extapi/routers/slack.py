from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.gate import gate, gate_passthrough
from extapi.models.passthrough import PassthroughRequest
from extapi.services import slack as slack_svc

router = APIRouter(prefix="/slack", tags=["slack"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.post("/messages")
@gate("slack", "POST", "/chat.postMessage")
async def post_message(request: Request):
    body = await request.json()
    client = request.app.state.slack_client
    caller_ip = request.client.host if request.client else None
    upstream = await slack_svc.post_message(client, body, caller_ip)
    return _forward(upstream)


@router.get("/channels/{channel_id}/history")
async def get_history(channel_id: str, request: Request):
    client = request.app.state.slack_client
    params = {}
    for key in ("cursor", "limit", "latest", "oldest"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await slack_svc.get_history(client, channel_id, params or None)
    return _forward(upstream)


@router.get("/channels/{channel_id}/replies")
async def get_replies(channel_id: str, ts: str, request: Request):
    client = request.app.state.slack_client
    params = {}
    for key in ("cursor", "limit"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await slack_svc.get_replies(client, channel_id, ts, params or None)
    return _forward(upstream)


@router.get("/channels")
async def list_channels(request: Request):
    client = request.app.state.slack_client
    params = {}
    for key in ("cursor", "limit", "types"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await slack_svc.list_channels(client, params or None)
    return _forward(upstream)


@router.post("/passthrough")
@gate_passthrough("slack")
async def slack_passthrough(payload: PassthroughRequest, request: Request):
    client = request.app.state.slack_client
    caller_ip = request.client.host if request.client else None
    upstream = await slack_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
