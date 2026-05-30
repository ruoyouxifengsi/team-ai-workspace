import docx

from app.tools._helpers import file_disk_path, require_visible, truncate_text
from app.tools.registry import register_tool


@register_tool(
    name="read_docx",
    description="Read a .docx Word document and return its paragraph text.",
    parameters={
        "type": "object",
        "properties": {"file_id": {"type": "integer"}},
        "required": ["file_id"],
    },
)
def read_docx(file_id: int, *, db, settings, user_id: int, user_role: str) -> dict:
    row = require_visible(db, file_id, user_id, user_role)
    path = file_disk_path(settings, row)
    d = docx.Document(str(path))
    text = "\n".join(p.text for p in d.paragraphs)
    return {"name": row.original_name, "content": truncate_text(text)}
