from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from app.auth.schemas import LoginRequest, LoginResponse, UserOut
from app.auth.service import create_session, revoke_session, verify_password
from app.config import Settings
from app.deps import current_user, get_db, get_settings_dep  # noqa: B008
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
):
    user = db.query(User).filter_by(username=payload.username).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    user.last_login_at = datetime.utcnow()
    db.commit()
    token = create_session(db, user_id=user.id, ttl_hours=settings.session_ttl_hours)
    return LoginResponse(
        token=token,
        user=UserOut(id=user.id, username=user.username, role=user.role),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):  # noqa: B008
    return UserOut(id=user.id, username=user.username, role=user.role)


@router.post("/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None),
    db: DbSession = Depends(get_db),  # noqa: B008
):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    revoke_session(db, authorization[7:])
    return Response(status_code=204)
