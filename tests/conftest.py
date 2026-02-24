import pytest
import httpx
import respx
from httpx import ASGITransport

from extapi.main import app
from extapi.settings import Settings


@pytest.fixture
async def client():
    settings = Settings()
    app.state.settings = settings

    with respx.mock(assert_all_called=False, assert_all_mocked=False) as mock:
        app.state.jira_client = httpx.AsyncClient(
            base_url=settings.jira_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )
        app.state.bitbucket_client = httpx.AsyncClient(
            base_url=settings.bitbucket_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )
        app.state.slack_client = httpx.AsyncClient(
            base_url=settings.slack_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )
        app.state.gmail_client = httpx.AsyncClient(
            base_url=settings.gmail_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )
        app.state.gdrive_client = httpx.AsyncClient(
            base_url=settings.gdrive_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )
        app.state.gcalendar_client = httpx.AsyncClient(
            base_url=settings.gcalendar_base_url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c, mock

        await app.state.jira_client.aclose()
        await app.state.bitbucket_client.aclose()
        await app.state.slack_client.aclose()
        await app.state.gmail_client.aclose()
        await app.state.gdrive_client.aclose()
        await app.state.gcalendar_client.aclose()
