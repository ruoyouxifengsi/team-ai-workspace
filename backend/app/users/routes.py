from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from app.deps import get_db, require_admin
from app.models import User
from app.users.schemas import CreateUserRequest, UpdatePasswordRequest, UserOut
from app.users.service import UsernameTaken, create_user, delete_user, list_users, set_password

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def _to_out(u: User) -> UserOut:
    return UserOut(id=u.id, username=u.username, role=u.role, daily_token_used=u.daily_token_used)


@router.get("", response_model=list[UserOut])
def get_all(db: DbSession = Depends(get_db), _admin: User = Depends(require_admin)):  # noqa: B008
    return [_to_out(u) for u in list_users(db)]


@router.post("", response_model=UserOut, status_code=201)
def create(
    payload: CreateUserRequest,
    db: DbSession = Depends(get_db),  # noqa: B008
    _admin: User = Depends(require_admin),  # noqa: B008
):
    try:
        u = create_user(db, username=payload.username, password=payload.password, role=payload.role)
    except UsernameTaken as err:
        raise HTTPException(status.HTTP_409_CONFLICT, "username already taken") from err
    return _to_out(u)


@router.delete("/{user_id}", status_code=204)
def delete(
    user_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    _admin: User = Depends(require_admin),  # noqa: B008
):
    if not delete_user(db, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return Response(status_code=204)


@router.put("/{user_id}/password", status_code=204)
def reset_password(
    user_id: int,
    payload: UpdatePasswordRequest,
    db: DbSession = Depends(get_db),  # noqa: B008
    _admin: User = Depends(require_admin),  # noqa: B008
):
    if not set_password(db, user_id, payload.password):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return Response(status_code=204)


class QuotaIn(BaseModel):
    daily_token_quota: int = Field(ge=0)


@router.put("/{user_id}/quota")
def update_quota(
    user_id: int,
    body: QuotaIn,
    db: DbSession = Depends(get_db),  # noqa: B008
    _admin: User = Depends(require_admin),  # noqa: B008
):
    from app.users.service import set_quota
    ok = set_quota(db, user_id, body.daily_token_quota)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return {"id": user_id, "daily_token_quota": body.daily_token_quota}
