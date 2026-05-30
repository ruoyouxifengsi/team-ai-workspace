import pytest
from pydantic import ValidationError


def test_settings_load_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_TTL_HOURS", "24")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    from cryptography.fernet import Fernet
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())

    from app.config import Settings
    s = Settings()
    assert s.database_url == "sqlite:///./test.db"
    assert s.data_dir == str(tmp_path)
    assert s.session_ttl_hours == 24
    assert s.admin_username == "admin"
    assert s.cors_origins == ["http://localhost:5173", "http://localhost:3000"]


def test_settings_missing_admin_password_raises(monkeypatch):
    monkeypatch.delenv("ADMIN_INITIAL_PASSWORD", raising=False)
    from app.config import Settings
    with pytest.raises(ValidationError):
        Settings()
