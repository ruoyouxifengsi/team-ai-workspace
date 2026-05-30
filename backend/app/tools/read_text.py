from app.tools._helpers import file_disk_path, require_visible, truncate_text
from app.tools.registry import register_tool


@register_tool(
    name="read_text",
    description="Read a plain-text file (txt, md, csv, json, etc.) by file_id.",
    parameters={
        "type": "object",
        "properties": {
            "file_id": {"type": "integer", "description": "File id from list_files"},
        },
        "required": ["file_id"],
    },
)
def read_text(file_id: int, *, db, settings, user_id: int, user_role: str) -> dict:
    row = require_visible(db, file_id, user_id, user_role)
    path = file_disk_path(settings, row)
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return {"name": row.original_name, "content": truncate_text(text)}
