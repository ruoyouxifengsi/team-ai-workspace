import io

import docx

from app.files.service import save_file
from app.tools.read_docx import read_docx


def _save_docx(text: str, name: str = "doc.docx", owner: str = "alice"):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username=owner).one()
    settings = get_settings()
    buf = io.BytesIO()
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    d.save(buf)
    buf.seek(0)
    row = save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
                    original_name=name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    content=buf)
    return db, settings, user, row


def test_read_docx_returns_paragraphs(client, member_token, env):
    db, settings, user, row = _save_docx("hello\nworld")
    out = read_docx(file_id=row.id, db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert out["name"] == "doc.docx"
    assert "hello" in out["content"]
    assert "world" in out["content"]
