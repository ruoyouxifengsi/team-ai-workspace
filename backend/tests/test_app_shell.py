import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "secret123")
    from cryptography.fernet import Fernet
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    from app.main import create_app
    return TestClient(create_app())


def test_healthz(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cors_header_present(client):
    r = client.options(
        "/api/healthz",
        headers={"Origin": "http://localhost:5173",
                 "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" in {h.lower() for h in r.headers.keys()}
