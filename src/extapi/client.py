import httpx

from extapi.settings import Settings


def make_jira_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.jira_base_url,
        auth=(settings.jira_user_email, settings.jira_api_token),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def make_bitbucket_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.bitbucket_base_url,
        auth=(settings.bitbucket_username, settings.bitbucket_app_password),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def make_slack_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.slack_base_url,
        headers={
            "Authorization": f"Bearer {settings.slack_bot_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def make_gmail_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.gmail_base_url,
        headers={
            "Authorization": f"Bearer {settings.google_access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def make_gdrive_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.gdrive_base_url,
        headers={
            "Authorization": f"Bearer {settings.google_access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def make_gcalendar_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.gcalendar_base_url,
        headers={
            "Authorization": f"Bearer {settings.google_access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
