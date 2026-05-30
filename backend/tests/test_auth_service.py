from datetime import datetime, timedelta


def test_hash_and_verify_password():
    from app.auth.service import hash_password, verify_password
    h = hash_password("hello123")
    assert h != "hello123"
    assert verify_password("hello123", h) is True
    assert verify_password("wrong", h) is False


def test_hash_password_different_salts():
    from app.auth.service import hash_password
    a = hash_password("same")
    b = hash_password("same")
    assert a != b


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    from app import db as db_mod
    engine = db_mod.make_engine(f"sqlite:///{tmp_path}/s.db")
    db_mod.init_schema(engine)
    Session = db_mod.make_session_factory(engine)
    from app.models import User
    with Session() as s:
        u = User(username="u", password_hash="h", role="member")
        s.add(u)
        s.commit()
        s.refresh(u)
        uid = u.id
    return Session, uid


def test_create_session_returns_token_with_ttl(tmp_path, monkeypatch):
    Session, uid = _setup(tmp_path, monkeypatch)
    from app.auth.service import create_session
    with Session() as s:
        tok = create_session(s, user_id=uid, ttl_hours=2)
        assert len(tok) >= 32
        from app.models import SessionRow
        row = s.get(SessionRow, tok)
        assert row is not None
        assert row.user_id == uid
        assert row.expires_at > datetime.utcnow() + timedelta(minutes=119)


def test_resolve_session_returns_user(tmp_path, monkeypatch):
    Session, uid = _setup(tmp_path, monkeypatch)
    from app.auth.service import create_session, resolve_session
    with Session() as s:
        tok = create_session(s, user_id=uid, ttl_hours=1)
        user = resolve_session(s, tok)
        assert user is not None
        assert user.id == uid


def test_resolve_session_expired_returns_none(tmp_path, monkeypatch):
    Session, uid = _setup(tmp_path, monkeypatch)
    from app.auth.service import resolve_session
    from app.models import SessionRow
    with Session() as s:
        s.add(SessionRow(token="expired", user_id=uid,
                         expires_at=datetime.utcnow() - timedelta(seconds=1)))
        s.commit()
        assert resolve_session(s, "expired") is None


def test_revoke_session_removes_row(tmp_path, monkeypatch):
    Session, uid = _setup(tmp_path, monkeypatch)
    from app.auth.service import create_session, resolve_session, revoke_session
    with Session() as s:
        tok = create_session(s, user_id=uid, ttl_hours=1)
        revoke_session(s, tok)
        assert resolve_session(s, tok) is None
