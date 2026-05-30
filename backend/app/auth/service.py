import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy.orm import Session as DbSession

from app.models import SessionRow, User


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_session(db: DbSession, user_id: int, ttl_hours: int) -> str:
    token = secrets.token_urlsafe(48)
    row = SessionRow(
        token=token, user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
    )
    db.add(row)
    db.commit()
    return token


def resolve_session(db: DbSession, token: str) -> User | None:
    row = db.get(SessionRow, token)
    if row is None or row.expires_at <= datetime.utcnow():
        return None
    return db.get(User, row.user_id)


def revoke_session(db: DbSession, token: str) -> None:
    row = db.get(SessionRow, token)
    if row is not None:
        db.delete(row)
        db.commit()
