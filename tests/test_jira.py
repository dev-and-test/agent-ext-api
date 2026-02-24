import pytest

JIRA = "https://yourco.atlassian.net"


@pytest.mark.asyncio
async def test_create_issue(client):
    c, mock = client
    mock.post(f"{JIRA}/rest/api/3/issue").respond(201, json={"id": "1", "key": "PROJ-1"})
    resp = await c.post("/jira/issues", json={"fields": {"summary": "Test"}})
    assert resp.status_code == 201
    assert resp.json()["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_get_issue(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(
        200, json={"key": "PROJ-1", "fields": {}}
    )
    resp = await c.get("/jira/issues/PROJ-1")
    assert resp.status_code == 200
    assert resp.json()["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_get_issue_with_params(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(200, json={"key": "PROJ-1"})
    resp = await c.get("/jira/issues/PROJ-1?fields=summary&expand=changelog")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_issue(client):
    c, mock = client
    mock.put(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(204)
    resp = await c.put(
        "/jira/issues/PROJ-1", json={"fields": {"summary": "Updated"}}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_issue(client):
    c, mock = client
    mock.delete(f"{JIRA}/rest/api/3/issue/PROJ-1").respond(204)
    resp = await c.delete("/jira/issues/PROJ-1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_changelog(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1/changelog").respond(
        200, json={"values": []}
    )
    resp = await c.get("/jira/issues/PROJ-1/changelog")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_search(client):
    c, mock = client
    mock.post(f"{JIRA}/rest/api/3/search").respond(200, json={"issues": []})
    resp = await c.post("/jira/search", json={"jql": "project = PROJ"})
    assert resp.status_code == 200
    assert resp.json()["issues"] == []


@pytest.mark.asyncio
async def test_get_comments(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/issue/PROJ-1/comment").respond(
        200, json={"comments": []}
    )
    resp = await c.get("/jira/issues/PROJ-1/comments")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_comment(client):
    c, mock = client
    mock.post(f"{JIRA}/rest/api/3/issue/PROJ-1/comment").respond(
        201, json={"id": "100"}
    )
    resp = await c.post("/jira/issues/PROJ-1/comments", json={"body": "Hello"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_comment(client):
    c, mock = client
    mock.put(f"{JIRA}/rest/api/3/issue/PROJ-1/comment/100").respond(
        200, json={"id": "100"}
    )
    resp = await c.put(
        "/jira/issues/PROJ-1/comments/100", json={"body": "Updated"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_comment(client):
    c, mock = client
    mock.delete(f"{JIRA}/rest/api/3/issue/PROJ-1/comment/100").respond(204)
    resp = await c.delete("/jira/issues/PROJ-1/comments/100")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/field").respond(200, json=[{"id": "summary"}])
    resp = await c.post(
        "/jira/passthrough",
        json={"method": "GET", "path": "/rest/api/3/field"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.get(f"{JIRA}/rest/api/3/issue/BAD-1").respond(
        404, json={"errorMessages": ["Issue does not exist"]}
    )
    resp = await c.get("/jira/issues/BAD-1")
    assert resp.status_code == 404
