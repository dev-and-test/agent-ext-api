import pytest

BB = "https://api.bitbucket.org/2.0"


@pytest.mark.asyncio
async def test_list_repos(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws").respond(200, json={"values": []})
    resp = await c.get("/bitbucket/repos/myws")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_repo(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws/myrepo").respond(
        200, json={"slug": "myrepo"}
    )
    resp = await c.get("/bitbucket/repos/myws/myrepo")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "myrepo"


@pytest.mark.asyncio
async def test_list_branches(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws/myrepo/refs/branches").respond(
        200, json={"values": []}
    )
    resp = await c.get("/bitbucket/repos/myws/myrepo/branches")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_pullrequests(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws/myrepo/pullrequests").respond(
        200, json={"values": []}
    )
    resp = await c.get("/bitbucket/repos/myws/myrepo/pullrequests")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_pullrequest(client):
    c, mock = client
    mock.post(f"{BB}/repositories/myws/myrepo/pullrequests").respond(
        201, json={"id": 1, "title": "My PR"}
    )
    resp = await c.post(
        "/bitbucket/repos/myws/myrepo/pullrequests",
        json={"title": "My PR", "source": {"branch": {"name": "feature"}}},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_get_pullrequest(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws/myrepo/pullrequests/1").respond(
        200, json={"id": 1}
    )
    resp = await c.get("/bitbucket/repos/myws/myrepo/pullrequests/1")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_pullrequest(client):
    c, mock = client
    mock.put(f"{BB}/repositories/myws/myrepo/pullrequests/1").respond(
        200, json={"id": 1, "title": "Updated"}
    )
    resp = await c.put(
        "/bitbucket/repos/myws/myrepo/pullrequests/1",
        json={"title": "Updated"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_merge_pullrequest(client):
    c, mock = client
    mock.post(f"{BB}/repositories/myws/myrepo/pullrequests/1/merge").respond(
        200, json={"state": "MERGED"}
    )
    resp = await c.post("/bitbucket/repos/myws/myrepo/pullrequests/1/merge")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{BB}/user").respond(200, json={"username": "me"})
    resp = await c.post(
        "/bitbucket/passthrough",
        json={"method": "GET", "path": "/user"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.get(f"{BB}/repositories/myws/nope").respond(
        404, json={"error": {"message": "Repository not found"}}
    )
    resp = await c.get("/bitbucket/repos/myws/nope")
    assert resp.status_code == 404
