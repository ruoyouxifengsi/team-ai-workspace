import io

from sqlalchemy import text

from app.files.service import delete_file, save_file


def test_saving_public_file_adds_to_fts(client, admin_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    admin = db.query(User).filter_by(username="admin").one()
    row = save_file(db, settings, owner_id=None, uploaded_by=admin.id,
                    original_name="readme.txt", mime="text/plain",
                    content=io.BytesIO(b"public manual content"))
    n = db.execute(
        text("SELECT count(*) FROM public_kb_fts WHERE file_id = :id"),
        {"id": row.id},
    ).scalar()
    assert n == 1


def test_personal_file_not_in_fts(client, member_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    user = db.query(User).filter_by(username="alice").one()
    row = save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
                    original_name="mine.txt", mime="text/plain",
                    content=io.BytesIO(b"private"))
    n = db.execute(
        text("SELECT count(*) FROM public_kb_fts WHERE file_id = :id"),
        {"id": row.id},
    ).scalar()
    assert n == 0


def test_deleting_public_file_removes_from_fts(client, admin_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    admin = db.query(User).filter_by(username="admin").one()
    row = save_file(db, settings, owner_id=None, uploaded_by=admin.id,
                    original_name="doomed.txt", mime="text/plain",
                    content=io.BytesIO(b"bye"))
    delete_file(db, settings, row.id)
    n = db.execute(
        text("SELECT count(*) FROM public_kb_fts WHERE file_id = :id"),
        {"id": row.id},
    ).scalar()
    assert n == 0
