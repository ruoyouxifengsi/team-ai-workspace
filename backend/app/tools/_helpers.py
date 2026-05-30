import io
from pathlib import Path

from sqlalchemy.orm import Session as DbSession

from app.files.service import get_file_if_visible, open_file, save_file
from app.models import FileRow

READ_TRUNCATE_BYTES = 50_000
WRITE_MAX_BYTES = 50 * 1024 * 1024


def truncate_text(s: str, limit: int = READ_TRUNCATE_BYTES) -> str:
    if len(s.encode("utf-8")) <= limit:
        return s
    head = s.encode("utf-8")[:limit].decode("utf-8", errors="ignore")
    return head + "\n\n[...truncated]"


def require_visible(db: DbSession, file_id: int, user_id: int, user_role: str) -> FileRow:
    row = get_file_if_visible(db, file_id, user_id, user_role)
    if row is None:
        raise ValueError(f"file_id {file_id} not found or not visible")
    return row


def write_personal(
    db: DbSession,
    settings,
    *,
    user_id: int,
    name: str,
    content_bytes: bytes,
    mime: str,
) -> FileRow:
    if len(content_bytes) > WRITE_MAX_BYTES:
        raise ValueError(f"content exceeds {WRITE_MAX_BYTES} bytes")
    return save_file(
        db, settings,
        owner_id=user_id, uploaded_by=user_id,
        original_name=name, mime=mime,
        content=io.BytesIO(content_bytes),
    )


def file_disk_path(settings, row: FileRow) -> Path:
    return open_file(settings, row)
