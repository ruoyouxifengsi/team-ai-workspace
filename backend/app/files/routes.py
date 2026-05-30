import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DbSession

from app.config import Settings
from app.deps import current_user, get_db, get_settings_dep
from app.files.schemas import FileListResponse, FileOut
from app.files.service import (
    delete_file,
    get_file_if_visible,
    list_public_files,
    list_user_files,
    open_file,
    save_file,
)
from app.models import FileRow, User

router = APIRouter(prefix="/api/files", tags=["files"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
BLOCKED_SUFFIXES = {".exe", ".sh", ".py", ".bat", ".cmd", ".js", ".ps1"}


def _to_out(row: FileRow) -> FileOut:
    return FileOut(
        id=row.id, name=row.original_name, size=row.size, mime=row.mime,
        uploaded_at=row.uploaded_at, is_public=(row.owner_id is None),
    )


@router.get("", response_model=FileListResponse)
def list_files(
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    personal = [_to_out(f) for f in list_user_files(db, user.id)]
    public = [_to_out(f) for f in list_public_files(db)]
    return FileListResponse(personal=personal, public=public)


@router.post("", response_model=FileOut, status_code=201)
async def upload(
    file: UploadFile = File(...),  # noqa: B008
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix in BLOCKED_SUFFIXES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"file type {suffix} not allowed")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large")
    row = save_file(
        db, settings,
        owner_id=user.id, uploaded_by=user.id,
        original_name=file.filename or "unnamed",
        mime=file.content_type or "application/octet-stream",
        content=io.BytesIO(content),
    )
    return _to_out(row)


@router.get("/{file_id}")
def download(
    file_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    row = get_file_if_visible(db, file_id, user.id, user.role)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return FileResponse(
        open_file(settings, row),
        filename=row.original_name,
        media_type=row.mime,
    )


@router.post("/{file_id}/publish", response_model=FileOut)
def publish(
    file_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    row = db.get(FileRow, file_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if row.owner_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "already public")
    if row.owner_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cannot publish others' files")
    src = Path(settings.data_dir) / row.path
    dst_dir = Path(settings.data_dir) / "public"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / Path(row.path).name
    if src.exists():
        src.rename(dst)
    row.path = str(dst.relative_to(Path(settings.data_dir)))
    row.owner_id = None
    db.commit()
    db.refresh(row)
    from app.tools.search_public import _extract_text, index_one_file
    body = _extract_text(Path(settings.data_dir) / row.path, row.mime)
    index_one_file(db.get_bind(), row.id, row.original_name, body)
    return _to_out(row)


@router.delete("/{file_id}", status_code=204)
def delete(
    file_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    row = get_file_if_visible(db, file_id, user.id, user.role)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if row.owner_id is None and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "only admin can delete public files")
    delete_file(db, settings, file_id)
    return Response(status_code=204)
