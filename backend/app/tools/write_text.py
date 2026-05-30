from app.tools._helpers import write_personal
from app.tools.registry import register_tool


@register_tool(
    name="write_text",
    description=(
        "Write a plain-text file to the user's personal workspace. "
        "Use a clear, unique filename to avoid overwriting existing files."
    ),
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filename incl. extension (e.g. plan.md)"},
            "content": {"type": "string", "description": "Text content"},
        },
        "required": ["name", "content"],
    },
)
def write_text(name: str, content: str, *, db, settings, user_id: int, user_role: str) -> dict:
    row = write_personal(
        db, settings, user_id=user_id, name=name,
        content_bytes=content.encode("utf-8"), mime="text/plain",
    )
    return {"file_id": row.id, "name": row.original_name}
