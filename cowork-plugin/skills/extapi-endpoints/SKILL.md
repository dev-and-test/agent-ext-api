---
name: extapi-endpoints
description: >
  Use this skill when the user asks to interact with Jira, Bitbucket, Slack,
  Gmail, Google Drive, or Google Calendar. Also use when the user mentions
  "extapi", "external API proxy", or needs to call any of these services
  without credentials. The proxy runs locally and all requests are
  pre-authenticated — no tokens needed in your calls.
version: 0.1.0
---

# extapi — External API Proxy

extapi is a local HTTP proxy running at `http://127.0.0.1:11583` that provides authenticated access to external services. All requests are pre-authenticated — no tokens or credentials needed in your calls.

## Quick Reference

| Service | Prefix | Key endpoints |
|---------|--------|--------------|
| Jira | `/jira` | issues, search, comments |
| Bitbucket | `/bitbucket` | repos, branches, pull requests |
| Slack | `/slack` | messages, channels, threads |
| Gmail | `/gmail` | messages, drafts, attachments |
| Google Drive | `/gdrive` | files, folders, downloads |
| Google Calendar | `/gcalendar` | calendars, events |

Every service also has a `POST /{service}/passthrough` endpoint for arbitrary API calls not covered by the named endpoints.

## Health Check

```
GET /health → {"status": "ok"}
```

Always check health first if you're unsure whether the proxy is running.

## Passthrough Request Format

All services support a passthrough endpoint for API calls not covered by named endpoints:

```json
POST /{service}/passthrough
{
  "method": "GET",
  "path": "/api/path/here",
  "body": {},
  "params": {"key": "value"}
}
```

The `path` is relative to the service's upstream base URL. The `body` and `params` fields are optional.

## Full Endpoint Reference

See **`references/endpoints.md`** for complete endpoint tables, query parameters, and curl examples for every service.
