import io

import openpyxl

from app.files.service import save_file
from app.tools.read_xlsx import read_xlsx


def _save_xlsx(sheets: dict[str, list[list]], name: str = "data.xlsx"):
    from app.config import get_settings
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    user = db.query(User).filter_by(username="alice").one()
    settings = get_settings()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sname, rows in sheets.items():
        ws = wb.create_sheet(sname)
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    row = save_file(db, settings, owner_id=user.id, uploaded_by=user.id,
                    original_name=name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    content=buf)
    return db, settings, user, row


def test_read_all_sheets(client, member_token, env):
    db, settings, user, row = _save_xlsx({
        "Names": [["A", "B"], [1, 2]],
        "Other": [["x"], ["y"]],
    })
    out = read_xlsx(file_id=row.id, db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert out["name"] == "data.xlsx"
    assert set(out["sheets"].keys()) == {"Names", "Other"}
    assert out["sheets"]["Names"] == [["A", "B"], [1, 2]]


def test_read_specific_sheet(client, member_token, env):
    db, settings, user, row = _save_xlsx({
        "Names": [["A"]],
        "Other": [["x"], ["y"]],
    })
    out = read_xlsx(file_id=row.id, sheet="Other", db=db, settings=settings,
                    user_id=user.id, user_role="member")
    assert list(out["sheets"].keys()) == ["Other"]
    assert out["sheets"]["Other"] == [["x"], ["y"]]
