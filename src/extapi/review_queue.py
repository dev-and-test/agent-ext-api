from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import aiosqlite
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse, Response

logger = structlog.get_logger()

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS review_queue (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    decided_at  TEXT,
    service     TEXT NOT NULL,
    method      TEXT NOT NULL,
    upstream_path TEXT NOT NULL,
    body        TEXT,
    params      TEXT,
    caller_ip   TEXT,
    endpoint    TEXT NOT NULL,
    response_status INTEGER,
    response_body   TEXT
);
"""


async def init_db(path: str) -> aiosqlite.Connection:
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute(_CREATE_TABLE)
    await db.commit()
    return db


async def maybe_enqueue(
    request: Request,
    service: str,
    method: str,
    upstream_path: str,
    body: dict | None = None,
    params: dict[str, str] | None = None,
    endpoint: str = "",
) -> Response | None:
    settings = request.app.state.settings

    if not settings.requires_approval(service, method):
        return None

    caller_ip = request.client.host if request.client else None
    item_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()

    db: aiosqlite.Connection = request.app.state.review_db
    await db.execute(
        """INSERT INTO review_queue
           (id, created_at, status, service, method, upstream_path, body, params, caller_ip, endpoint)
           VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?)""",
        (
            item_id,
            now,
            service,
            method.upper(),
            upstream_path,
            json.dumps(body) if body is not None else None,
            json.dumps(params) if params is not None else None,
            caller_ip,
            endpoint,
        ),
    )
    await db.commit()

    await logger.ainfo(
        "mutation_enqueued",
        review_id=item_id,
        service=service,
        method=method,
        upstream_path=upstream_path,
        caller_ip=caller_ip,
    )

    return JSONResponse(
        status_code=202,
        content={
            "queued": True,
            "review_id": item_id,
            "message": f"{method.upper()} requires approval",
            "service": service,
            "path": upstream_path,
        },
    )


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    d = dict(row)
    for key in ("body", "params"):
        if d.get(key) is not None:
            d[key] = json.loads(d[key])
    return d


async def list_items(
    db: aiosqlite.Connection,
    status: str | None = None,
    service: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM review_queue WHERE 1=1"
    binds: list[str] = []
    if status:
        query += " AND status = ?"
        binds.append(status)
    if service:
        query += " AND service = ?"
        binds.append(service)
    query += " ORDER BY created_at DESC"
    async with db.execute(query, binds) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def get_item(db: aiosqlite.Connection, item_id: str) -> dict | None:
    async with db.execute("SELECT * FROM review_queue WHERE id = ?", (item_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row) if row else None


async def reject_item(db: aiosqlite.Connection, item_id: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE review_queue SET status = 'rejected', decided_at = ? WHERE id = ? AND status = 'pending'",
        (now, item_id),
    )
    await db.commit()
    return await get_item(db, item_id)


async def delete_item(db: aiosqlite.Connection, item_id: str) -> bool:
    cur = await db.execute("DELETE FROM review_queue WHERE id = ?", (item_id,))
    await db.commit()
    return cur.rowcount > 0


def _get_client(app, service: str):
    return getattr(app.state, f"{service}_client")


async def approve_item(app, item_id: str) -> dict | None:
    db: aiosqlite.Connection = app.state.review_db
    item = await get_item(db, item_id)
    if not item or item["status"] != "pending":
        return item

    client = _get_client(app, item["service"])
    body = item["body"]
    params = item["params"]

    resp = await client.request(
        item["method"],
        item["upstream_path"],
        json=body,
        params=params,
    )

    now = datetime.now(timezone.utc).isoformat()
    resp_body: str | None = None
    try:
        resp_body = resp.text
    except Exception:
        pass

    await db.execute(
        """UPDATE review_queue
           SET status = 'approved', decided_at = ?, response_status = ?, response_body = ?
           WHERE id = ?""",
        (now, resp.status_code, resp_body, item_id),
    )
    await db.commit()

    await logger.ainfo(
        "mutation_approved",
        review_id=item_id,
        service=item["service"],
        method=item["method"],
        upstream_path=item["upstream_path"],
        upstream_status=resp.status_code,
    )

    return await get_item(db, item_id)
