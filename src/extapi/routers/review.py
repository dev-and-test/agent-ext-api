from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from extapi.review_queue import approve_item, delete_item, get_item, list_items, reject_item

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue")
async def list_queue(
    request: Request,
    status: str | None = Query(None, pattern="^(pending|approved|rejected)$"),
    service: str | None = Query(None),
):
    db = request.app.state.review_db
    items = await list_items(db, status=status, service=service)
    return JSONResponse(content={"items": items, "count": len(items)})


@router.get("/queue/{item_id}")
async def get_queue_item(item_id: str, request: Request):
    db = request.app.state.review_db
    item = await get_item(db, item_id)
    if not item:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    return JSONResponse(content=item)


@router.post("/queue/{item_id}/approve")
async def approve_queue_item(item_id: str, request: Request):
    db = request.app.state.review_db
    item = await get_item(db, item_id)
    if not item:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    if item["status"] != "pending":
        return JSONResponse(
            status_code=409,
            content={"error": "not_pending", "status": item["status"]},
        )
    result = await approve_item(request.app, item_id)
    return JSONResponse(content=result)


@router.post("/queue/{item_id}/reject")
async def reject_queue_item(item_id: str, request: Request):
    db = request.app.state.review_db
    item = await get_item(db, item_id)
    if not item:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    if item["status"] != "pending":
        return JSONResponse(
            status_code=409,
            content={"error": "not_pending", "status": item["status"]},
        )
    result = await reject_item(db, item_id)
    return JSONResponse(content=result)


@router.delete("/queue/{item_id}")
async def delete_queue_item(item_id: str, request: Request):
    db = request.app.state.review_db
    deleted = await delete_item(db, item_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    return JSONResponse(content={"deleted": True})
