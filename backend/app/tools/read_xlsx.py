import openpyxl

from app.tools._helpers import file_disk_path, require_visible
from app.tools.registry import register_tool


@register_tool(
    name="read_xlsx",
    description=(
        "Read an .xlsx spreadsheet. Returns a dict of sheet name -> 2D list of cell values. "
        "Pass `sheet` to limit to one sheet."
    ),
    parameters={
        "type": "object",
        "properties": {
            "file_id": {"type": "integer"},
            "sheet": {"type": "string", "description": "Optional single sheet name"},
        },
        "required": ["file_id"],
    },
)
def read_xlsx(
    file_id: int, sheet: str | None = None,
    *, db, settings, user_id: int, user_role: str,
) -> dict:
    row = require_visible(db, file_id, user_id, user_role)
    path = file_disk_path(settings, row)
    wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    sheets: dict[str, list[list]] = {}
    targets = [sheet] if sheet else wb.sheetnames
    for sname in targets:
        if sname not in wb.sheetnames:
            raise ValueError(f"sheet not found: {sname}")
        ws = wb[sname]
        sheets[sname] = [list(r) for r in ws.iter_rows(values_only=True)]
    return {"name": row.original_name, "sheets": sheets}
