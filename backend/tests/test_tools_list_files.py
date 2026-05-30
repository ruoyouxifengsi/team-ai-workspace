import io

from app.files.service import save_file
from app.tools.list_files import list_files


def test_list_personal_files(client, member_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username="alice").one()
    settings = get_settings()
    save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
              original_name="a.txt", mime="text/plain",
              content=io.BytesIO(b"hello"))

    out = list_files(area="personal", db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert isinstance(out, list)
    assert any(f["name"] == "a.txt" for f in out)
    assert "file_id" in out[0]
    assert "size" in out[0]
    assert "uploaded_at" in out[0]


def test_list_public_files(client, admin_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    admin = db.query(User).filter_by(username="admin").one()
    settings = get_settings()
    save_file(db, settings, owner_id=None, uploaded_by=admin.id,
              original_name="public.txt", mime="text/plain",
              content=io.BytesIO(b"pub"))

    out = list_files(area="public", db=db, settings=settings,
                    user_id=admin.id, user_role="admin")
    assert any(f["name"] == "public.txt" for f in out)


def test_list_invalid_area(client, member_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username="alice").one()
    import pytest
    with pytest.raises(ValueError):
        list_files(area="bogus", db=db, settings=get_settings(),
                   user_id=user.id, user_role="member")
