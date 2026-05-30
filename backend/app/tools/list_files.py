from app.files.service import list_public_files, list_user_files
from app.tools.registry import register_tool


@register_tool(
    name="list_files",
    description=(
        "List files in the user's personal workspace or the public knowledge "
        "base. Returns file_id, name, size, uploaded_at for each."
    ),
    parameters={
        "type": "object",
        "properties": {
            "area": {
                "type": "string",
                "enum": ["personal", "public"],
                "description": "Which area to list",
            },
        },
        "required": ["area"],
    },
)
def list_files(area: str, *, db, settings, user_id: int, user_role: str) -> list[dict]:
    if area == "personal":
        rows = list_user_files(db, user_id)
    elif area == "public":
        rows = list_public_files(db)
    else:
        raise ValueError(f"unknown area: {area}")
    return [
        {
            "file_id": r.id,
            "name": r.original_name,
            "size": r.size,
            "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in rows
    ]
