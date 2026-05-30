from datetime import datetime


def _setup(tmp_path):
    from app import db as db_mod
    engine = db_mod.make_engine(f"sqlite:///{tmp_path}/m.db")
    db_mod.init_schema(engine)
    Session = db_mod.make_session_factory(engine)
    return Session


def test_user_create_and_query(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    Session = _setup(tmp_path)
    from app.models import User
    with Session() as s:
        u = User(username="alice", password_hash="h", role="member")
        s.add(u)
        s.commit()
        s.refresh(u)
        assert u.id is not None
        assert u.created_at is not None
        assert u.role == "member"


def test_session_row_links_to_user(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    Session = _setup(tmp_path)
    from app.models import SessionRow, User
    with Session() as s:
        u = User(username="bob", password_hash="h", role="member")
        s.add(u)
        s.commit()
        sr = SessionRow(token="tok123", user_id=u.id, expires_at=datetime(2099, 1, 1))
        s.add(sr)
        s.commit()
        found = s.get(SessionRow, "tok123")
        assert found.user_id == u.id


def test_file_row_owner_null_means_public(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    Session = _setup(tmp_path)
    from app.models import FileRow
    with Session() as s:
        f = FileRow(owner_id=None, path="public/a.txt", original_name="a.txt",
                    size=1, mime="text/plain", uploaded_by=1)
        s.add(f)
        s.commit()
        s.refresh(f)
        assert f.id is not None
        assert f.owner_id is None
