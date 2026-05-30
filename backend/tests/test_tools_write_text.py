import pytest

from app.tools.write_text import write_text


def _alice():
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    return db, get_settings(), db.query(User).filter_by(username="alice").one()


def test_write_creates_personal_file(client, member_token, env):
    db, settings, user = _alice()
    out = write_text(name="note.md", content="# hi", db=db, settings=settings,
                     user_id=user.id, user_role="member")
    assert "file_id" in out
    assert out["name"] == "note.md"

    from app.files.service import get_file_if_visible
    row = get_file_if_visible(db, out["file_id"], user.id, "member")
    assert row is not None
    assert row.owner_id == user.id


def test_write_rejects_oversize(client, member_token, env):
    db, settings, user = _alice()
    huge = "a" * (51 * 1024 * 1024)
    with pytest.raises(ValueError):
        write_text(name="huge.txt", content=huge, db=db, settings=settings,
                   user_id=user.id, user_role="member")
