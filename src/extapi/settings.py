from pydantic_settings import BaseSettings


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

    # Server
    host: str = "127.0.0.1"
    port: int = 11583

    model_config = {"env_prefix": "EXTAPI_"}
