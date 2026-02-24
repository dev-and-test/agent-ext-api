# External APIs for Agents

Authenticated proxy API developed primarily to keep credentials and secrets away from AI agents while still allowing them to integrate with external APIs and services.

This API sits between your agents (or any application) and upstream APIs (Jira, Bitbucket, Slack, Gmail, Google Drive, Google Calendar), handling authentication so that API tokens, passwords, and OAuth credentials never need to be exposed to the calling agent. As long as your agents don't have access to the directory where you have the environment variables for thsi project, you're offered some (better than nothing) protection against prompt injection attacks that might steal your tokens and keys. Your data can still be exfiltrated, but you won't be giving someone more than a one time data dump.

## Supported services

| Service          | Auth method                  |
|------------------|------------------------------|
| Jira             | Basic (email + API token)    |
| Bitbucket        | Basic (username + app password) |
| Slack            | Bearer token                 |
| Gmail            | Bearer token (Google OAuth)  |
| Google Drive     | Bearer token (Google OAuth)  |
| Google Calendar  | Bearer token (Google OAuth)  |

## Quick start

### Running directly

```bash
# Install dependencies
uv sync

# Set credentials
export EXTAPI_JIRA_USER_EMAIL=you@company.com
export EXTAPI_JIRA_API_TOKEN=your-token
export EXTAPI_SLACK_BOT_TOKEN=xoxb-...
export EXTAPI_GOOGLE_ACCESS_TOKEN=ya29...

# Start the server (defaults to 127.0.0.1:11583)
uv run extapi
```

### Installing as a dependency

Add extapi to another project:

```bash
# From git
uv add git+https://github.com/dev-and-test/agent-ext-api.git

# From a local path
uv add /path/to/agent-ext-api
```

Then start it programmatically:

```python
from extapi import serve

# Uses EXTAPI_* env vars for all configuration
serve()

# Or override host/port directly
serve(host="0.0.0.0", port=9000)
```

You can also import the FastAPI app to mount it inside another application:

```python
from extapi import app

parent_app.mount("/proxy", app)
```

### Running multiple instances with different credentials

Each instance reads from `EXTAPI_*` environment variables, so you can run multiple instances on different ports with different credentials:

```bash
# Instance 1 — Team A's Jira + Slack
EXTAPI_PORT=11001 \
EXTAPI_JIRA_USER_EMAIL=team-a@company.com \
EXTAPI_JIRA_API_TOKEN=token-a \
EXTAPI_SLACK_BOT_TOKEN=xoxb-team-a \
  extapi &

# Instance 2 — Team B's Jira + Slack
EXTAPI_PORT=11002 \
EXTAPI_JIRA_USER_EMAIL=team-b@company.com \
EXTAPI_JIRA_API_TOKEN=token-b \
EXTAPI_SLACK_BOT_TOKEN=xoxb-team-b \
  extapi &
```

## Configuration

All settings are controlled via environment variables with the `EXTAPI_` prefix.

### Server

| Variable | Default | Description |
|---|---|---|
| `EXTAPI_HOST` | `127.0.0.1` | Bind address |
| `EXTAPI_PORT` | `11583` | Bind port |

### Credentials

| Variable | Description |
|---|---|
| `EXTAPI_JIRA_BASE_URL` | Jira instance URL (default: `https://yourco.atlassian.net`) |
| `EXTAPI_JIRA_USER_EMAIL` | Jira user email |
| `EXTAPI_JIRA_API_TOKEN` | Jira API token |
| `EXTAPI_BITBUCKET_BASE_URL` | Bitbucket API URL (default: `https://api.bitbucket.org/2.0`) |
| `EXTAPI_BITBUCKET_USERNAME` | Bitbucket username |
| `EXTAPI_BITBUCKET_APP_PASSWORD` | Bitbucket app password |
| `EXTAPI_SLACK_BASE_URL` | Slack API URL (default: `https://slack.com/api`) |
| `EXTAPI_SLACK_BOT_TOKEN` | Slack bot token |
| `EXTAPI_GMAIL_BASE_URL` | Gmail API URL (default: `https://gmail.googleapis.com`) |
| `EXTAPI_GDRIVE_BASE_URL` | Google Drive API URL (default: `https://www.googleapis.com`) |
| `EXTAPI_GCALENDAR_BASE_URL` | Google Calendar API URL (default: `https://www.googleapis.com`) |
| `EXTAPI_GOOGLE_ACCESS_TOKEN` | Google OAuth access token (shared by Gmail, Drive, Calendar) |

### Feature flags

| Variable | Default | Description |
|---|---|---|
| `EXTAPI_DRY_RUN_DELETES` | `false` | When enabled, all DELETE requests return a dummy response instead of hitting the upstream API |

## API overview

Each service exposes typed endpoints for common operations plus a generic passthrough:

```
GET  /health

# Jira
POST   /jira/issues
GET    /jira/issues/{key}
PUT    /jira/issues/{key}
DELETE /jira/issues/{key}
POST   /jira/search
...
POST   /jira/passthrough

# Bitbucket
GET    /bitbucket/repos/{workspace}
POST   /bitbucket/repos/{workspace}/{repo}/pullrequests
...
POST   /bitbucket/passthrough

# Slack
POST   /slack/messages
GET    /slack/channels/{id}/history
...
POST   /slack/passthrough

# Gmail, Google Drive, Google Calendar — similar pattern
```

The passthrough endpoint accepts any method/path combination:

```json
POST /jira/passthrough
{
  "method": "GET",
  "path": "/rest/api/3/myself",
  "params": {"expand": "groups"}
}
```

## Teaching AI agents to use extapi

The repository includes a skill file at `.claude/skills/extapi.md` that documents every endpoint, parameter, and includes curl examples. To teach another AI agent how to use this API, copy the skill file into your project's skills directory. Once present, your agent will automatically know how to call all extapi endpoints without needing credentials — it just sends requests to the local proxy.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check
```
