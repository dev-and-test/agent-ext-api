import pytest

GDRIVE = "https://www.googleapis.com"


@pytest.mark.asyncio
async def test_list_files(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files").respond(
        200, json={"files": [{"id": "f1", "name": "doc.txt"}]}
    )
    resp = await c.get("/gdrive/files?q=name+contains+'test'")
    assert resp.status_code == 200
    assert resp.json()["files"][0]["id"] == "f1"


@pytest.mark.asyncio
async def test_list_files_with_params(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files").respond(
        200, json={"files": []}
    )
    resp = await c.get("/gdrive/files?pageSize=10&orderBy=modifiedTime&fields=files(id,name)")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_file(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files/file123").respond(
        200, json={"id": "file123", "name": "readme.md", "mimeType": "text/plain"}
    )
    resp = await c.get("/gdrive/files/file123")
    assert resp.status_code == 200
    assert resp.json()["name"] == "readme.md"


@pytest.mark.asyncio
async def test_get_file_with_fields(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files/file123").respond(
        200, json={"id": "file123", "name": "readme.md"}
    )
    resp = await c.get("/gdrive/files/file123?fields=id,name")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_download_file(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files/file123").respond(
        200, content=b"file content bytes", headers={"content-type": "application/octet-stream"}
    )
    resp = await c.get("/gdrive/files/file123/download")
    assert resp.status_code == 200
    assert resp.content == b"file content bytes"
    assert resp.headers["content-type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_create_file(client):
    c, mock = client
    mock.post(f"{GDRIVE}/drive/v3/files").respond(
        200, json={"id": "newfile", "name": "folder1", "mimeType": "application/vnd.google-apps.folder"}
    )
    resp = await c.post(
        "/gdrive/files",
        json={"name": "folder1", "mimeType": "application/vnd.google-apps.folder"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == "newfile"


@pytest.mark.asyncio
async def test_update_file_rename(client):
    c, mock = client
    mock.patch(f"{GDRIVE}/drive/v3/files/file123").respond(
        200, json={"id": "file123", "name": "renamed.txt"}
    )
    resp = await c.patch(
        "/gdrive/files/file123",
        json={"name": "renamed.txt"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "renamed.txt"


@pytest.mark.asyncio
async def test_update_file_move(client):
    c, mock = client
    mock.patch(f"{GDRIVE}/drive/v3/files/file123").respond(
        200, json={"id": "file123", "parents": ["folder2"]}
    )
    resp = await c.patch(
        "/gdrive/files/file123?addParents=folder2&removeParents=folder1",
        json={},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_passthrough(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/about").respond(
        200, json={"kind": "drive#about", "user": {"displayName": "Test"}}
    )
    resp = await c.post(
        "/gdrive/passthrough",
        json={"method": "GET", "path": "/drive/v3/about", "params": {"fields": "user"}},
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "drive#about"


@pytest.mark.asyncio
async def test_passthrough_mutation(client):
    c, mock = client
    mock.delete(f"{GDRIVE}/drive/v3/files/file123").respond(204)
    resp = await c.post(
        "/gdrive/passthrough",
        json={"method": "DELETE", "path": "/drive/v3/files/file123"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_upstream_error_forwarded(client):
    c, mock = client
    mock.get(f"{GDRIVE}/drive/v3/files/bad").respond(
        404, json={"error": {"code": 404, "message": "File not found"}}
    )
    resp = await c.get("/gdrive/files/bad")
    assert resp.status_code == 404
