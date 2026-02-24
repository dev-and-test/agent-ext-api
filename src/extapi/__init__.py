from extapi.main import app
from extapi.settings import Settings


def serve(host: str | None = None, port: int | None = None, **kwargs) -> None:
    """Start the extapi server.

    Host/port resolution order: explicit args > env vars > defaults.
    All extra kwargs are forwarded to ``uvicorn.run``.
    """
    import uvicorn

    settings = Settings()
    uvicorn.run(
        app,
        host=host or settings.host,
        port=port or settings.port,
        **kwargs,
    )
