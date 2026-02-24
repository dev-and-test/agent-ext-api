# extapi Endpoint Reference

Base URL: `http://127.0.0.1:11583`

---

## Jira (`/jira`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| POST | `/jira/issues` | — | JSON (issue fields) | Create issue |
| GET | `/jira/issues/{issue_key}` | `fields`, `expand` | — | Get issue |
| PUT | `/jira/issues/{issue_key}` | — | JSON (fields to update) | Update issue |
| DELETE | `/jira/issues/{issue_key}` | — | — | Delete issue |
| GET | `/jira/issues/{issue_key}/changelog` | — | — | Get issue changelog |
| GET | `/jira/issues/{issue_key}/comments` | — | — | List comments |
| POST | `/jira/issues/{issue_key}/comments` | — | JSON (comment body) | Add comment |
| PUT | `/jira/issues/{issue_key}/comments/{comment_id}` | — | JSON (comment body) | Update comment |
| DELETE | `/jira/issues/{issue_key}/comments/{comment_id}` | — | — | Delete comment |
| POST | `/jira/search` | — | JSON (`{"jql": "...", ...}`) | Search issues via JQL |
| POST | `/jira/passthrough` | — | PassthroughRequest | Arbitrary Jira API call |

### Examples

```bash
# Search for open bugs assigned to me
curl http://127.0.0.1:11583/jira/search \
  -H 'Content-Type: application/json' \
  -d '{"jql": "assignee = currentUser() AND type = Bug AND status != Done"}'

# Get issue with specific fields
curl 'http://127.0.0.1:11583/jira/issues/PROJ-123?fields=summary,status,assignee'

# Add a comment
curl http://127.0.0.1:11583/jira/issues/PROJ-123/comments \
  -H 'Content-Type: application/json' \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Comment text"}]}]}}'
```

---

## Bitbucket (`/bitbucket`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| GET | `/bitbucket/repos/{workspace}` | — | — | List repos in workspace |
| GET | `/bitbucket/repos/{workspace}/{repo_slug}` | — | — | Get repo details |
| GET | `/bitbucket/repos/{workspace}/{repo_slug}/branches` | — | — | List branches |
| GET | `/bitbucket/repos/{workspace}/{repo_slug}/pullrequests` | — | — | List pull requests |
| POST | `/bitbucket/repos/{workspace}/{repo_slug}/pullrequests` | — | JSON (PR fields) | Create pull request |
| GET | `/bitbucket/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}` | — | — | Get PR details |
| PUT | `/bitbucket/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}` | — | JSON (fields to update) | Update PR |
| POST | `/bitbucket/repos/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge` | — | JSON (optional) | Merge PR |
| POST | `/bitbucket/passthrough` | — | PassthroughRequest | Arbitrary Bitbucket API call |

### Examples

```bash
# List repos
curl http://127.0.0.1:11583/bitbucket/repos/myworkspace

# Create a pull request
curl http://127.0.0.1:11583/bitbucket/repos/myworkspace/myrepo/pullrequests \
  -H 'Content-Type: application/json' \
  -d '{"title": "Fix bug", "source": {"branch": {"name": "fix/bug"}}, "destination": {"branch": {"name": "main"}}}'
```

---

## Slack (`/slack`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| POST | `/slack/messages` | — | JSON (`channel`, `text`, etc.) | Post message |
| GET | `/slack/channels/{channel_id}/history` | `cursor`, `limit`, `latest`, `oldest` | — | Get channel history |
| GET | `/slack/channels/{channel_id}/replies` | `ts` (required), `cursor`, `limit` | — | Get thread replies |
| GET | `/slack/channels` | `cursor`, `limit`, `types` | — | List channels |
| POST | `/slack/passthrough` | — | PassthroughRequest | Arbitrary Slack API call |

### Examples

```bash
# Post a message
curl http://127.0.0.1:11583/slack/messages \
  -H 'Content-Type: application/json' \
  -d '{"channel": "C123ABC", "text": "Hello from extapi"}'

# Get recent messages in a channel
curl 'http://127.0.0.1:11583/slack/channels/C123ABC/history?limit=10'

# Get thread replies
curl 'http://127.0.0.1:11583/slack/channels/C123ABC/replies?ts=1234567890.123456'
```

---

## Gmail (`/gmail`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| GET | `/gmail/messages` | `q`, `maxResults`, `pageToken`, `labelIds` | — | Search/list emails |
| GET | `/gmail/messages/{message_id}` | `format`, `metadataHeaders` | — | Get full email content |
| GET | `/gmail/messages/{message_id}/attachments/{attachment_id}` | — | — | Get attachment (base64url) |
| POST | `/gmail/drafts` | — | JSON (draft object with `message.raw`) | Create draft |
| POST | `/gmail/passthrough` | — | PassthroughRequest | Arbitrary Gmail API call |

### Examples

```bash
# Search for unread emails
curl 'http://127.0.0.1:11583/gmail/messages?q=is:unread&maxResults=10'

# Get full email content
curl 'http://127.0.0.1:11583/gmail/messages/18f1a2b3c4d5e6f7?format=full'

# Get attachment
curl http://127.0.0.1:11583/gmail/messages/18f1a2b3c4d5e6f7/attachments/ANGjdJ8

# Create a draft
curl http://127.0.0.1:11583/gmail/drafts \
  -H 'Content-Type: application/json' \
  -d '{"message": {"raw": "<base64url-encoded RFC 2822 message>"}}'

# List labels via passthrough
curl http://127.0.0.1:11583/gmail/passthrough \
  -H 'Content-Type: application/json' \
  -d '{"method": "GET", "path": "/gmail/v1/users/me/labels"}'
```

---

## Google Drive (`/gdrive`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| GET | `/gdrive/files` | `q`, `fields`, `pageSize`, `pageToken`, `orderBy` | — | Search/list files |
| GET | `/gdrive/files/{file_id}` | `fields` | — | Get file metadata |
| GET | `/gdrive/files/{file_id}/download` | — | — | Download file content (raw bytes) |
| POST | `/gdrive/files` | — | JSON (`name`, `mimeType`, `parents`) | Create file/folder metadata |
| PATCH | `/gdrive/files/{file_id}` | `addParents`, `removeParents` | JSON (`name`, etc.) | Rename or move file |
| POST | `/gdrive/passthrough` | — | PassthroughRequest | Arbitrary Drive API call |

### Examples

```bash
# Search for files
curl 'http://127.0.0.1:11583/gdrive/files?q=name+contains+%27report%27&pageSize=10'

# Get file metadata with specific fields
curl 'http://127.0.0.1:11583/gdrive/files/1AbC2dEfG?fields=id,name,mimeType,size'

# Download file content
curl http://127.0.0.1:11583/gdrive/files/1AbC2dEfG/download --output file.pdf

# Create a folder
curl http://127.0.0.1:11583/gdrive/files \
  -H 'Content-Type: application/json' \
  -d '{"name": "New Folder", "mimeType": "application/vnd.google-apps.folder"}'

# Rename a file
curl -X PATCH http://127.0.0.1:11583/gdrive/files/1AbC2dEfG \
  -H 'Content-Type: application/json' \
  -d '{"name": "new-name.txt"}'

# Move a file to a different folder
curl -X PATCH 'http://127.0.0.1:11583/gdrive/files/1AbC2dEfG?addParents=FOLDER_ID&removeParents=OLD_FOLDER_ID' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

---

## Google Calendar (`/gcalendar`)

| Method | Path | Query Params | Body | Purpose |
|--------|------|-------------|------|---------|
| GET | `/gcalendar/calendars` | `maxResults`, `pageToken` | — | List user's calendars |
| GET | `/gcalendar/calendars/{calendar_id}/events` | `q`, `timeMin`, `timeMax`, `maxResults`, `pageToken`, `singleEvents`, `orderBy` | — | List events |
| GET | `/gcalendar/events/{calendar_id}/{event_id}` | — | — | Get single event |
| POST | `/gcalendar/calendars/{calendar_id}/events` | — | JSON (event object) | Create event |
| PATCH | `/gcalendar/events/{calendar_id}/{event_id}` | — | JSON (fields to update) | Update event |
| DELETE | `/gcalendar/events/{calendar_id}/{event_id}` | — | — | Delete event |
| POST | `/gcalendar/passthrough` | — | PassthroughRequest | Arbitrary Calendar API call |

### Examples

```bash
# List all calendars
curl http://127.0.0.1:11583/gcalendar/calendars

# List today's events (sorted by start time)
curl 'http://127.0.0.1:11583/gcalendar/calendars/primary/events?timeMin=2026-02-24T00:00:00Z&timeMax=2026-02-25T00:00:00Z&singleEvents=true&orderBy=startTime'

# Search events by keyword
curl 'http://127.0.0.1:11583/gcalendar/calendars/primary/events?q=standup'

# Get a single event
curl http://127.0.0.1:11583/gcalendar/events/primary/event123

# Create an event
curl http://127.0.0.1:11583/gcalendar/calendars/primary/events \
  -H 'Content-Type: application/json' \
  -d '{"summary": "Team Sync", "start": {"dateTime": "2026-02-25T10:00:00Z"}, "end": {"dateTime": "2026-02-25T10:30:00Z"}}'

# Update an event summary
curl -X PATCH http://127.0.0.1:11583/gcalendar/events/primary/event123 \
  -H 'Content-Type: application/json' \
  -d '{"summary": "Renamed Meeting"}'

# Delete an event
curl -X DELETE http://127.0.0.1:11583/gcalendar/events/primary/event123

# Get calendar colors via passthrough
curl http://127.0.0.1:11583/gcalendar/passthrough \
  -H 'Content-Type: application/json' \
  -d '{"method": "GET", "path": "/calendar/v3/colors"}'
```
