import io

from app.files.service import save_file
from app.tools.search_public import reindex_public_kb, search_public


def test_search_public_finds_by_filename(client, admin_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    admin = db.query(User).filter_by(username="admin").one()
    save_file(db, settings, owner_id=None, uploaded_by=admin.id,
              original_name="评委想要什么.txt", mime="text/plain",
              content=io.BytesIO("评委关心：1) 实践成果 2) 队员配合".encode("utf-8")))
    reindex_public_kb(db.get_bind())

    hits = search_public(query="评委", db=db, settings=settings,
                         user_id=admin.id, user_role="admin")
    assert len(hits) >= 1
    assert "评委" in hits[0]["name"] or "评委" in hits[0]["excerpt"]
    assert "file_id" in hits[0]


def test_search_public_finds_by_content(client, admin_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    admin = db.query(User).filter_by(username="admin").one()
    save_file(db, settings, owner_id=None, uploaded_by=admin.id,
              original_name="历届方案.txt", mime="text/plain",
              content=io.BytesIO("第十届夏令营主题为乡村振兴".encode("utf-8")))
    reindex_public_kb(db.get_bind())
    hits = search_public(query="乡村振兴", db=db, settings=settings,
                         user_id=admin.id, user_role="admin")
    assert len(hits) >= 1
