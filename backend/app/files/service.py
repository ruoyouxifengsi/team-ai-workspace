import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session as DbSession

from app.config import Settings
from app.files.storage import sanitize_filename, user_dir
from app.models import FileRow


def save_file(
    db: DbSession,
    settings: Settings,
    *,
    owner_id: int | None,
    uploaded_by: int,
    original_name: str,
    mime: str,
    content: BinaryIO,
) -> FileRow:
    safe_name = sanitize_filename(original_name)
    if owner_id:
        target_dir = user_dir(settings.data_dir, owner_id)
    else:
        target_dir = Path(settings.data_dir, "public")
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    target = target_dir / stored_name
    tmp = target.with_suffix(target.suffix + ".part")
    with tmp.open("wb") as out:
        shutil.copyfileobj(content, out)
    tmp.rename(target)
    rel_path = str(target.relative_to(settings.data_dir))
    size = target.stat().st_size
    row = FileRow(
        owner_id=owner_id, path=rel_path, original_name=safe_name,
        size=size, mime=mime, uploaded_by=uploaded_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if row.owner_id is None:
        from app.tools.search_public import _extract_text, index_one_file
        body = _extract_text(Path(settings.data_dir) / row.path, row.mime)
        index_one_file(db.get_bind(), row.id, row.original_name, body)
    return row


def list_user_files(db: DbSession, user_id: int) -> list[FileRow]:
    return (
        db.query(FileRow)
        .filter(FileRow.owner_id == user_id)
        .order_by(FileRow.uploaded_at.desc())
        .all()
    )


def list_public_files(db: DbSession) -> list[FileRow]:
    return (
        db.query(FileRow)
        .filter(FileRow.owner_id.is_(None))
        .order_by(FileRow.uploaded_at.desc())
        .all()
    )


def open_file(settings: Settings, row: FileRow) -> Path:
    return Path(settings.data_dir) / row.path


def get_file_if_visible(
    db: DbSession,
    file_id: int,
    user_id: int,
    user_role: str = "member",
) -> FileRow | None:
    row = db.get(FileRow, file_id)
    if row is None:
        return None
    if row.owner_id is None:  # public
        return row
    if user_role == "admin":
        return row
    if row.owner_id == user_id:
        return row
    return None


def delete_file(db: DbSession, settings: Settings, file_id: int) -> bool:
    row = db.get(FileRow, file_id)
    if row is None:
        return False
    if row.owner_id is None:
        from app.tools.search_public import remove_from_index
        remove_from_index(db.get_bind(), file_id)
    path = Path(settings.data_dir) / row.path
    if path.exists():
        path.unlink()
    db.delete(row)
    db.commit()
    return True
