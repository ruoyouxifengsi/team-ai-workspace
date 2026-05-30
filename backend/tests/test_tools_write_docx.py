import docx

from app.files.service import get_file_if_visible, open_file
from app.tools.write_docx import write_docx


def test_write_docx_creates_file_with_markdown_content(client, member_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    settings = get_settings()
    user = db.query(User).filter_by(username="alice").one()

    md = "# Title\n\nFirst paragraph.\n\n- bullet one\n- bullet two"
    out = write_docx(name="plan.docx", markdown=md, db=db, settings=settings,
                     user_id=user.id, user_role="member")

    assert out["name"] == "plan.docx"
    row = get_file_if_visible(db, out["file_id"], user.id, "member")
    assert row is not None
    path = open_file(settings, row)
    d = docx.Document(str(path))
    joined = "\n".join(p.text for p in d.paragraphs)
    assert "Title" in joined
    assert "First paragraph." in joined
    assert "bullet one" in joined
