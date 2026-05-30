def test_login_success_returns_token(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"


def test_login_wrong_password_returns_401(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "WRONG"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401(client):
    r = client.post("/api/auth/login", json={"username": "noone", "password": "x"})
    assert r.status_code == 401


def test_login_updates_last_login_at(client, env):
    client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    from app.deps import _session_factory
    with _session_factory() as s:
        from app.models import User
        u = s.query(User).filter_by(username="admin").one()
        assert u.last_login_at is not None


def test_logout_revokes_token(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "secret123"})
    tok = r.json()["token"]
    r2 = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 204
    r3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r3.status_code == 401


def test_logout_without_token_returns_401(client):
    r = client.post("/api/auth/logout")
    assert r.status_code == 401
