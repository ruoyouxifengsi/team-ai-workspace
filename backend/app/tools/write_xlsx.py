import io

import openpyxl

from app.tools._helpers import write_personal
from app.tools.registry import register_tool


@register_tool(
    name="write_xlsx",
    description=(
        "Create an .xlsx spreadsheet from a dict mapping sheet name -> "
        "2D array of cell values. Saved to the user's personal workspace."
    ),
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "sheets": {
                "type": "object",
                "description": "Object: sheet_name -> array of rows",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "array"},
                },
            },
        },
        "required": ["name", "sheets"],
    },
)
def write_xlsx(name: str, sheets: dict, *, db, settings, user_id: int, user_role: str) -> dict:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sname, rows in sheets.items():
        ws = wb.create_sheet(sname)
        for r in rows:
            ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    row = write_personal(
        db, settings, user_id=user_id, name=name,
        content_bytes=buf.getvalue(),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return {"file_id": row.id, "name": row.original_name}
