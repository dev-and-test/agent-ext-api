from pydantic import model_validator
from pydantic_settings import BaseSettings


def _parse_methods(raw: str) -> frozenset[str]:
    if not raw:
        return frozenset()
    return frozenset(m.strip().upper() for m in raw.split(",") if m.strip())


class Settings(BaseSettings):
    # Jira
    jira_base_url: str = "https://yourco.atlassian.net"
    jira_user_email: str = ""
    jira_api_token: str = ""

    # Bitbucket
    bitbucket_base_url: str = "https://api.bitbucket.org/2.0"
    bitbucket_username: str = ""
    bitbucket_app_password: str = ""

    # Slack
    slack_base_url: str = "https://slack.com/api"
    slack_bot_token: str = ""

    # Gmail
    gmail_base_url: str = "https://gmail.googleapis.com"
    google_access_token: str = ""

    # Google Drive
    gdrive_base_url: str = "https://www.googleapis.com"

    # Google Calendar
    gcalendar_base_url: str = "https://www.googleapis.com"

    # Feature flags
    dry_run_deletes: bool = False

    # Per-service approval gates — comma-separated HTTP methods, e.g. "post,put,delete"
    # Empty string (default) means no approval required for that service.
    require_approval_jira: str = ""
    require_approval_bitbucket: str = ""
    require_approval_slack: str = ""
    require_approval_gmail: str = ""
    require_approval_gdrive: str = ""
    require_approval_gcalendar: str = ""
    review_db_path: str = "extapi_review.db"

    # Pre-parsed lookup table: {service: frozenset[method]}
    _approval_gates: dict[str, frozenset[str]] = {}

    @model_validator(mode="after")
    def _build_approval_gates(self) -> "Settings":
        self._approval_gates = {
            svc: _parse_methods(getattr(self, f"require_approval_{svc}"))
            for svc in ("jira", "bitbucket", "slack", "gmail", "gdrive", "gcalendar")
        }
        return self

    def requires_approval(self, service: str, method: str) -> bool:
        return method in self._approval_gates.get(service, frozenset())

    # Server
    host: str = "127.0.0.1"
    port: int = 11583

    model_config = {"env_prefix": "EXTAPI_"}
