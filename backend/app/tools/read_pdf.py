from pypdf import PdfReader

from app.tools._helpers import file_disk_path, require_visible, truncate_text
from app.tools.registry import register_tool


@register_tool(
    name="read_pdf",
    description="Extract text from a PDF file by file_id.",
    parameters={
        "type": "object",
        "properties": {"file_id": {"type": "integer"}},
        "required": ["file_id"],
    },
)
def read_pdf(file_id: int, *, db, settings, user_id: int, user_role: str) -> dict:
    row = require_visible(db, file_id, user_id, user_role)
    path = file_disk_path(settings, row)
    reader = PdfReader(str(path))
    parts: list[str] = []
    for p in reader.pages:
        try:
            parts.append(p.extract_text() or "")
        except Exception:
            parts.append("")
    text = "\n\n".join(parts)
    return {
        "name": row.original_name,
        "content": truncate_text(text),
        "pages": len(reader.pages),
    }
