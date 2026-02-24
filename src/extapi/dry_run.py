import structlog
from fastapi import Request
from fastapi.responses import JSONResponse, Response

logger = structlog.get_logger()


async def maybe_block_delete(request: Request, service: str, path: str) -> Response | None:
    """If dry_run_deletes is enabled, log the attempt and return a dummy response.

    Returns ``None`` when the delete should proceed normally.
    """
    settings = request.app.state.settings
    if not settings.dry_run_deletes:
        return None

    caller_ip = request.client.host if request.client else None
    await logger.ainfo(
        "delete_blocked_dry_run",
        service=service,
        upstream_path=path,
        caller_ip=caller_ip,
    )
    return JSONResponse(
        status_code=200,
        content={
            "dry_run": True,
            "message": f"DELETE blocked by dry_run_deletes flag",
            "service": service,
            "path": path,
        },
    )
