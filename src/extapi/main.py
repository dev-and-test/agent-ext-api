from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from extapi.client import (
    make_bitbucket_client,
    make_gcalendar_client,
    make_gdrive_client,
    make_gmail_client,
    make_jira_client,
    make_slack_client,
)
from extapi.logging import setup_logging
from extapi.routers import bitbucket, gcalendar, gdrive, gmail, health, jira, slack
from extapi.settings import Settings

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    app.state.jira_client = make_jira_client(settings)
    app.state.bitbucket_client = make_bitbucket_client(settings)
    app.state.slack_client = make_slack_client(settings)
    app.state.gmail_client = make_gmail_client(settings)
    app.state.gdrive_client = make_gdrive_client(settings)
    app.state.gcalendar_client = make_gcalendar_client(settings)
    yield
    await app.state.jira_client.aclose()
    await app.state.bitbucket_client.aclose()
    await app.state.slack_client.aclose()
    await app.state.gmail_client.aclose()
    await app.state.gdrive_client.aclose()
    await app.state.gcalendar_client.aclose()


app = FastAPI(title="extapi", lifespan=lifespan)

app.include_router(health.router)
app.include_router(jira.router)
app.include_router(bitbucket.router)
app.include_router(slack.router)
app.include_router(gmail.router)
app.include_router(gdrive.router)
app.include_router(gcalendar.router)


@app.exception_handler(httpx.ConnectError)
async def upstream_connect_error(request: Request, exc: httpx.ConnectError):
    return JSONResponse(
        status_code=502,
        content={"error": "upstream_unreachable", "detail": str(exc)},
    )


@app.exception_handler(httpx.TimeoutException)
async def upstream_timeout(request: Request, exc: httpx.TimeoutException):
    return JSONResponse(
        status_code=504,
        content={"error": "upstream_timeout", "detail": str(exc)},
    )
