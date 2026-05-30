import io


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/f.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    from cryptography.fernet import Fernet
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    from app import db as db_mod
    from app.config import get_settings
    settings = get_settings()
    engine = db_mod.make_engine(settings.database_url)
    db_mod.init_schema(engine)
    Session = db_mod.make_session_factory(engine)
    from app.models import User
    with Session() as s:
        u = User(username="alice", password_hash="h", role="member")
        s.add(u)
        s.commit()
        s.refresh(u)
        uid = u.id
    return Session, settings, uid


def test_save_file_writes_to_disk_and_db(tmp_path, monkeypatch):
    Session, settings, uid = _setup(tmp_path, monkeypatch)
    from app.files.service import save_file
    with Session() as s:
        f = save_file(s, settings, owner_id=uid, uploaded_by=uid,
                      original_name="hello.txt", mime="text/plain",
                      content=io.BytesIO(b"hello"))
        assert f.id is not None
        assert f.size == 5
        from pathlib import Path
        assert Path(settings.data_dir, "users", str(uid), Path(f.path).name).exists()


def test_list_files_returns_owner_files(tmp_path, monkeypatch):
    Session, settings, uid = _setup(tmp_path, monkeypatch)
    from app.files.service import list_user_files, save_file
    with Session() as s:
        save_file(s, settings, owner_id=uid, uploaded_by=uid,
                  original_name="a.txt", mime="text/plain",
                  content=io.BytesIO(b"a"))
        save_file(s, settings, owner_id=uid, uploaded_by=uid,
                  original_name="b.txt", mime="text/plain",
                  content=io.BytesIO(b"b"))
        files = list_user_files(s, uid)
        assert len(files) == 2


def test_open_file_returns_bytes(tmp_path, monkeypatch):
    Session, settings, uid = _setup(tmp_path, monkeypatch)
    from app.files.service import open_file, save_file
    with Session() as s:
        f = save_file(s, settings, owner_id=uid, uploaded_by=uid,
                      original_name="x.txt", mime="text/plain",
                      content=io.BytesIO(b"world"))
        path = open_file(settings, f)
        assert path.read_bytes() == b"world"


def test_delete_file_removes_disk_and_row(tmp_path, monkeypatch):
    Session, settings, uid = _setup(tmp_path, monkeypatch)
    from app.files.service import delete_file, save_file
    from app.models import FileRow
    with Session() as s:
        f = save_file(s, settings, owner_id=uid, uploaded_by=uid,
                      original_name="y.txt", mime="text/plain",
                      content=io.BytesIO(b"x"))
        fid = f.id
        disk_path = s.get(FileRow, fid).path
        delete_file(s, settings, fid)
        from pathlib import Path
        assert not (Path(settings.data_dir) / disk_path).exists()
        assert s.get(FileRow, fid) is None
