from fastapi import APIRouter, Request
from fastapi.responses import Response

from extapi.gate import gate, gate_passthrough
from extapi.models.passthrough import PassthroughRequest
from extapi.services import gdrive as gdrive_svc

router = APIRouter(prefix="/gdrive", tags=["gdrive"])


def _forward(upstream) -> Response:
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.get("/files")
async def list_files(request: Request):
    client = request.app.state.gdrive_client
    params = {}
    for key in ("q", "fields", "pageSize", "pageToken", "orderBy"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gdrive_svc.list_files(client, params or None)
    return _forward(upstream)


@router.get("/files/{file_id}")
async def get_file(file_id: str, request: Request):
    client = request.app.state.gdrive_client
    params = {}
    for key in ("fields",):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gdrive_svc.get_file(client, file_id, params or None)
    return _forward(upstream)


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, request: Request):
    client = request.app.state.gdrive_client
    upstream = await gdrive_svc.download_file(client, file_id)
    return _forward(upstream)


@router.post("/files")
@gate("gdrive", "POST", "/drive/v3/files")
async def create_file(request: Request):
    body = await request.json()
    client = request.app.state.gdrive_client
    caller_ip = request.client.host if request.client else None
    upstream = await gdrive_svc.create_file(client, body, caller_ip)
    return _forward(upstream)


@router.patch("/files/{file_id}")
@gate("gdrive", "PATCH", "/drive/v3/files/{file_id}")
async def update_file(file_id: str, request: Request):
    body = await request.json()
    client = request.app.state.gdrive_client
    caller_ip = request.client.host if request.client else None
    params = {}
    for key in ("addParents", "removeParents"):
        val = request.query_params.get(key)
        if val is not None:
            params[key] = val
    upstream = await gdrive_svc.update_file(
        client, file_id, body, params or None, caller_ip
    )
    return _forward(upstream)


@router.post("/passthrough")
@gate_passthrough("gdrive")
async def gdrive_passthrough(payload: PassthroughRequest, request: Request):
    client = request.app.state.gdrive_client
    caller_ip = request.client.host if request.client else None
    upstream = await gdrive_svc.passthrough(
        client, payload.method, payload.path, payload.body, payload.params, caller_ip
    )
    return _forward(upstream)
