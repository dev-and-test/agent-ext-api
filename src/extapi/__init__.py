from extapi.main import app
from extapi.settings import Settings


def serve(
    host: str | None = None,
    port: int | None = None,
    env_file: str | None = None,
    **kwargs,
) -> None:
    """Start the extapi server.

    Args:
        host: Bind address. Falls back to EXTAPI_HOST env var, then 127.0.0.1.
        port: Bind port. Falls back to EXTAPI_PORT env var, then 11583.
        env_file: Path to a .env file to load settings from.
        **kwargs: Forwarded to ``uvicorn.run``.
    """
    import argparse
    import sys

    import uvicorn

    import extapi.main as _main

    # When called as a CLI entry point, parse args from sys.argv.
    # When called programmatically with explicit env_file, skip parsing.
    if env_file is None and sys.argv[1:]:
        parser = argparse.ArgumentParser(
            prog="extapi",
            description="Authenticated proxy API for enterprise SaaS tools",
        )
        parser.add_argument(
            "--env-file",
            metavar="PATH",
            help="path to a .env file to load settings from",
        )
        args, _ = parser.parse_known_args()
        env_file = args.env_file

    _main._env_file = env_file

    settings = Settings(_env_file=env_file) if env_file else Settings()
    uvicorn.run(
        app,
        host=host or settings.host,
        port=port or settings.port,
        **kwargs,
    )
