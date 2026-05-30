import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "secret123")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("SESSION_TTL_HOURS", "24")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    from cryptography.fernet import Fernet
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-team")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    return tmp_path


@pytest.fixture
def client(env):
    from app.main import create_app
    return TestClient(create_app())


@pytest.fixture
def db_session(env):
    from app.main import create_app
    create_app()
    from app.deps import _session_factory
    return _session_factory()


def _login(client, username: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def admin_token(client):
    return _login(client, "admin", "secret123")


@pytest.fixture
def member_token(client, admin_token):
    r = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "alice", "password": "alicepw", "role": "member"},
    )
    assert r.status_code == 201, r.text
    return _login(client, "alice", "alicepw")
