from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.auth.service import resolve_session
from app.models import User


def get_settings_dep():
    from app.config import get_settings
    return get_settings()


def get_db_factory():
    raise RuntimeError("get_db_factory not initialized; set in create_app")


_session_factory = None


def set_session_factory(factory):
    global _session_factory
    _session_factory = factory


def get_db():
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized")
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def current_user(
    authorization: str | None = Header(default=None),
    db: DbSession = Depends(get_db),  # noqa: B008
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing token")
    token = authorization[7:]
    user = resolve_session(db, token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    return user


def require_admin(user: User = Depends(current_user)) -> User:  # noqa: B008
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user
