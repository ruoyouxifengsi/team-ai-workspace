def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_list_users_requires_admin(client, member_token):
    r = client.get("/api/admin/users", headers=_auth(member_token))
    assert r.status_code == 403


def test_list_users_as_admin(client, admin_token):
    r = client.get("/api/admin/users", headers=_auth(admin_token))
    assert r.status_code == 200
    usernames = {u["username"] for u in r.json()}
    assert "admin" in usernames


def test_create_user_as_admin(client, admin_token):
    r = client.post(
        "/api/admin/users",
        headers=_auth(admin_token),
        json={"username": "bob", "password": "bobpw", "role": "member"},
    )
    assert r.status_code == 201
    assert r.json()["username"] == "bob"


def test_create_user_duplicate_rejected(client, admin_token):
    client.post("/api/admin/users", headers=_auth(admin_token),
                json={"username": "c", "password": "p", "role": "member"})
    r = client.post("/api/admin/users", headers=_auth(admin_token),
                    json={"username": "c", "password": "p2", "role": "member"})
    assert r.status_code == 409


def test_create_user_rejects_member(client, member_token):
    r = client.post("/api/admin/users", headers=_auth(member_token),
                    json={"username": "x", "password": "y", "role": "member"})
    assert r.status_code == 403


def test_delete_user(client, admin_token):
    r = client.post("/api/admin/users", headers=_auth(admin_token),
                    json={"username": "tmp", "password": "p", "role": "member"})
    uid = r.json()["id"]
    r2 = client.delete(f"/api/admin/users/{uid}", headers=_auth(admin_token))
    assert r2.status_code == 204
    r3 = client.get("/api/admin/users", headers=_auth(admin_token))
    assert "tmp" not in {u["username"] for u in r3.json()}


def test_delete_unknown_user_returns_404(client, admin_token):
    r = client.delete("/api/admin/users/99999", headers=_auth(admin_token))
    assert r.status_code == 404


def test_reset_password(client, admin_token):
    r = client.post("/api/admin/users", headers=_auth(admin_token),
                    json={"username": "rp", "password": "old", "role": "member"})
    uid = r.json()["id"]
    r2 = client.put(f"/api/admin/users/{uid}/password",
                    headers=_auth(admin_token), json={"password": "new"})
    assert r2.status_code == 204
    r3 = client.post("/api/auth/login", json={"username": "rp", "password": "old"})
    assert r3.status_code == 401
    r4 = client.post("/api/auth/login", json={"username": "rp", "password": "new"})
    assert r4.status_code == 200
