import io

from pypdf import PdfWriter

from app.files.service import save_file
from app.tools.read_pdf import read_pdf


def _make_pdf_bytes() -> bytes:
    # pypdf can't easily render text-only PDFs; use a minimal blank PDF.
    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_read_pdf_returns_pages_count(client, member_token, env):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username="alice").one()
    settings = get_settings()
    row = save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
                    original_name="x.pdf", mime="application/pdf",
                    content=io.BytesIO(_make_pdf_bytes()))
    out = read_pdf(file_id=row.id, db=db, settings=settings,
                   user_id=user.id, user_role="member")
    assert out["name"] == "x.pdf"
    assert out["pages"] == 1
    assert isinstance(out["content"], str)
