from sqlalchemy.orm import Session as DbSession

from app.auth.service import hash_password
from app.config import Settings
from app.models import User


def ensure_admin_exists(db: DbSession, settings: Settings) -> None:
    existing = db.query(User).filter_by(username=settings.admin_username).one_or_none()
    if existing is not None:
        return
    admin = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_initial_password),
        role="admin",
    )
    db.add(admin)
    db.commit()
