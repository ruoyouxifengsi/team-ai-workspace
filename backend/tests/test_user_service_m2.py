from app.config import get_settings
from app.crypto.fernet import decrypt
from app.models import User
from app.users.service import clear_personal_key, set_personal_key, set_quota


def test_set_personal_key_encrypts(client, member_token, env):
    from app.deps import _session_factory
    db = _session_factory()
    settings = get_settings()
    user = db.query(User).filter_by(username="alice").one()
    set_personal_key(db, user.id, "sk-real", settings.fernet_key.encode())
    db.refresh(user)
    assert user.personal_deepseek_key_enc is not None
    assert user.personal_deepseek_key_enc != "sk-real"
    assert decrypt(user.personal_deepseek_key_enc, settings.fernet_key.encode()) == "sk-real"


def test_clear_personal_key(client, member_token, env):
    from app.deps import _session_factory
    db = _session_factory()
    settings = get_settings()
    user = db.query(User).filter_by(username="alice").one()
    set_personal_key(db, user.id, "sk-x", settings.fernet_key.encode())
    clear_personal_key(db, user.id)
    db.refresh(user)
    assert user.personal_deepseek_key_enc is None


def test_set_quota(client, member_token, env):
    from app.deps import _session_factory
    db = _session_factory()
    user = db.query(User).filter_by(username="alice").one()
    set_quota(db, user.id, 3_000_000)
    db.refresh(user)
    assert user.daily_token_quota == 3_000_000
