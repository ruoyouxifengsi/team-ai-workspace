import io


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_upload_and_list(client, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("hello.txt", io.BytesIO(b"hi"), "text/plain")},
    )
    assert r.status_code == 201
    fid = r.json()["id"]

    r2 = client.get("/api/files", headers=_h(member_token))
    assert r2.status_code == 200
    ids = {f["id"] for f in r2.json()["personal"]}
    assert fid in ids


def test_download_returns_content(client, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("d.txt", io.BytesIO(b"download-me"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.get(f"/api/files/{fid}", headers=_h(member_token))
    assert r2.status_code == 200
    assert r2.content == b"download-me"


def test_delete_removes_file(client, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("d.txt", io.BytesIO(b"x"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.delete(f"/api/files/{fid}", headers=_h(member_token))
    assert r2.status_code == 204
    r3 = client.get(f"/api/files/{fid}", headers=_h(member_token))
    assert r3.status_code == 404


def test_cannot_access_other_users_file(client, admin_token, member_token):
    r = client.post(
        "/api/files",
        headers=_h(admin_token),
        files={"file": ("secret.txt", io.BytesIO(b"S"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.get(f"/api/files/{fid}", headers=_h(member_token))
    assert r2.status_code == 404


def test_admin_can_access_member_file(client, admin_token, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("m.txt", io.BytesIO(b"M"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.get(f"/api/files/{fid}", headers=_h(admin_token))
    assert r2.status_code == 200
    assert r2.content == b"M"


def test_upload_too_large_rejected(client, member_token, monkeypatch):
    import app.files.routes as routes_mod
    monkeypatch.setattr(routes_mod, "MAX_UPLOAD_BYTES", 10)
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("big.txt", io.BytesIO(b"x" * 100), "text/plain")},
    )
    assert r.status_code == 413


def test_upload_rejects_blacklisted_extension(client, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("evil.exe", io.BytesIO(b"M"), "application/octet-stream")},
    )
    assert r.status_code == 400


def test_member_can_publish_own_file(client, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.post(f"/api/files/{fid}/publish", headers=_h(member_token))
    assert r2.status_code == 200, r2.text
    assert r2.json()["is_public"] is True


def test_member_cannot_publish_others_file(client, admin_token, member_token):
    r = client.post(
        "/api/files",
        headers=_h(admin_token),
        files={"file": ("priv.txt", io.BytesIO(b"x"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.post(f"/api/files/{fid}/publish", headers=_h(member_token))
    assert r2.status_code == 403


def test_admin_can_publish_any_file(client, admin_token, member_token):
    r = client.post(
        "/api/files",
        headers=_h(member_token),
        files={"file": ("m.txt", io.BytesIO(b"M"), "text/plain")},
    )
    fid = r.json()["id"]
    r2 = client.post(f"/api/files/{fid}/publish", headers=_h(admin_token))
    assert r2.status_code == 200
    assert r2.json()["is_public"] is True
