import io

import pytest

from app.files.service import save_file
from app.tools.read_text import read_text


def _setup_user_file(name: str, content: bytes, owner: str = "alice"):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username=owner).one()
    settings = get_settings()
    row = save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
                    original_name=name, mime="text/plain",
                    content=io.BytesIO(content))
    return db, settings, user, row


def test_read_owned_file(client, member_token, env):
    db, settings, user, row = _setup_user_file("a.txt", b"hello world")
    out = read_text(file_id=row.id, db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert out == {"name": "a.txt", "content": "hello world"}


def test_read_other_users_file_rejected(client, admin_token, member_token, env):
    db, settings, alice, row = _setup_user_file("a.txt", b"secret", owner="alice")
    # Create bob
    from app.users.service import create_user
    bob = create_user(db, username="bob", password="pw", role="member")
    with pytest.raises(ValueError):
        read_text(file_id=row.id, db=db, settings=settings,
                  user_id=bob.id, user_role="member")


def test_read_truncates_large_file(client, member_token, env):
    big = b"a" * 60_000
    db, settings, user, row = _setup_user_file("big.txt", big)
    out = read_text(file_id=row.id, db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert out["content"].endswith("[...truncated]")
    assert len(out["content"].encode("utf-8")) < len(big)
