from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.auth.service import hash_password
from app.config import get_settings
from app.crypto.fernet import encrypt
from app.models import FileRow, SessionRow, User


class UsernameTaken(Exception):
    pass


def list_users(db: DbSession) -> list[User]:
    return db.query(User).order_by(User.id).all()


def create_user(db: DbSession, *, username: str, password: str, role: str) -> User:
    u = User(username=username, password_hash=hash_password(password), role=role)
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UsernameTaken(username) from None
    db.refresh(u)
    return u


def delete_user(db: DbSession, user_id: int) -> bool:
    u = db.get(User, user_id)
    if u is None:
        return False
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    files = db.query(FileRow).filter(FileRow.owner_id == user_id).all()
    for f in files:
        disk = data_dir / f.path
        if disk.exists():
            disk.unlink()
        db.delete(f)
    db.query(SessionRow).filter(SessionRow.user_id == user_id).delete()
    db.delete(u)
    db.commit()
    return True


def set_password(db: DbSession, user_id: int, new_password: str) -> bool:
    u = db.get(User, user_id)
    if u is None:
        return False
    u.password_hash = hash_password(new_password)
    db.commit()
    return True


def set_personal_key(db: DbSession, user_id: int, plain_key: str, fernet_key: bytes) -> bool:
    u = db.get(User, user_id)
    if u is None:
        return False
    u.personal_deepseek_key_enc = encrypt(plain_key, fernet_key)
    db.commit()
    return True


def clear_personal_key(db: DbSession, user_id: int) -> bool:
    u = db.get(User, user_id)
    if u is None:
        return False
    u.personal_deepseek_key_enc = None
    db.commit()
    return True


def set_quota(db: DbSession, user_id: int, quota: int) -> bool:
    u = db.get(User, user_id)
    if u is None:
        return False
    u.daily_token_quota = quota
    db.commit()
    return True
