from datetime import datetime, timedelta

from sqlalchemy.orm import Session as DbSession

from app.models import User


def _today_reset_threshold(now: datetime) -> datetime:
    """Return the most recent 4am Beijing instant (= 20:00 UTC previous day or today)."""
    today_bj_reset_utc = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now >= today_bj_reset_utc:
        return today_bj_reset_utc
    return today_bj_reset_utc - timedelta(days=1)


def check_and_reset(db: DbSession, user: User, *, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    threshold = _today_reset_threshold(now)
    if user.daily_token_reset_at is None or user.daily_token_reset_at < threshold:
        user.daily_token_used = 0
        user.daily_token_reset_at = now
        db.commit()


def charge(db: DbSession, user: User, tokens: int) -> None:
    user.daily_token_used = (user.daily_token_used or 0) + tokens
    db.commit()
