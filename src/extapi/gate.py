"""Decorators that intercept mutating requests for dry-run blocking and approval queuing.

Apply ``@gate`` to named mutating endpoints and ``@gate_passthrough`` to
passthrough endpoints.  All dry-run and review-queue logic is centralised
here — route handlers only contain the happy-path upstream call.
"""

from __future__ import annotations

import functools
import json

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from extapi.review_queue import maybe_enqueue


def _dry_run_response(service: str, path: str) -> Response:
    return JSONResponse(
        status_code=200,
        content={
            "dry_run": True,
            "message": "DELETE blocked by dry_run_deletes flag",
            "service": service,
            "path": path,
        },
    )


async def _check_gates(
    request: Request,
    service: str,
    method: str,
    upstream_path: str,
    body: dict | None,
    params: dict[str, str] | None,
) -> Response | None:
    settings = request.app.state.settings

    # Dry-run: immediate block for DELETEs, no DB involved.
    if method == "DELETE" and settings.dry_run_deletes:
        return _dry_run_response(service, upstream_path)

    # Approval queue: enqueue if the service/method combination requires it.
    return await maybe_enqueue(
        request, service, method, upstream_path,
        body=body, params=params,
    )


def gate(service: str, method: str, path_template: str):
    """Decorator for named mutating endpoints.

    ``path_template`` is an upstream path with ``{param}`` placeholders that
    are resolved from the handler's keyword arguments (FastAPI path params).

    Example::

        @router.post("/issues")
        @gate("jira", "POST", "/rest/api/3/issue")
        async def create_issue(request: Request):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(**kwargs):
            request: Request = kwargs["request"]
            upstream_path = path_template.format(**kwargs)

            body = None
            raw = await request.body()
            if raw:
                body = json.loads(raw)

            params = dict(request.query_params) or None

            blocked = await _check_gates(
                request, service, method.upper(), upstream_path, body, params,
            )
            if blocked:
                return blocked

            return await func(**kwargs)

        return wrapper

    return decorator


def gate_passthrough(service: str):
    """Decorator for passthrough endpoints.

    Reads ``method`` and ``path`` from the ``payload`` kwarg
    (a :class:`PassthroughRequest` instance) and gates non-GET requests.

    Example::

        @router.post("/passthrough")
        @gate_passthrough("jira")
        async def jira_passthrough(payload: PassthroughRequest, request: Request):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(**kwargs):
            request: Request = kwargs["request"]
            payload = kwargs["payload"]

            if payload.method != "GET":
                blocked = await _check_gates(
                    request, service, payload.method,
                    payload.path, payload.body, payload.params,
                )
                if blocked:
                    return blocked

            return await func(**kwargs)

        return wrapper

    return decorator
