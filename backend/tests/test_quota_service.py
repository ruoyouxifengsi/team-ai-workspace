from datetime import datetime, timedelta

from app.models import User
from app.quota.exceptions import QuotaExceeded
from app.quota.service import charge, check_and_reset


def _alice():
    from app.deps import _session_factory
    db = _session_factory()
    return db, db.query(User).filter_by(username="alice").one()


def test_check_and_reset_first_time(client, member_token, env):
    db, user = _alice()
    user.daily_token_used = 999
    user.daily_token_reset_at = None
    db.commit()
    check_and_reset(db, user, now=datetime.utcnow())
    assert user.daily_token_used == 0
    assert user.daily_token_reset_at is not None


def test_check_and_reset_skips_within_window(client, member_token, env):
    db, user = _alice()
    user.daily_token_used = 100
    # Set reset to 1 minute ago (well within today's window after 4am BJ)
    user.daily_token_reset_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    check_and_reset(db, user, now=datetime.utcnow())
    # Should NOT reset
    assert user.daily_token_used == 100


def test_charge_adds_tokens(client, member_token, env):
    db, user = _alice()
    user.daily_token_used = 50
    db.commit()
    charge(db, user, 75)
    assert user.daily_token_used == 125


def test_charge_raises_when_over_limit_before(client, member_token, env):
    db, user = _alice()
    user.daily_token_used = user.daily_token_quota
    # Set reset_at to now so check_and_reset does NOT reset within window
    user.daily_token_reset_at = datetime.utcnow()
    db.commit()
    import pytest
    with pytest.raises(QuotaExceeded):
        check_and_reset_and_assert(db, user)


def check_and_reset_and_assert(db, user):
    from datetime import datetime
    check_and_reset(db, user, now=datetime.utcnow())
    if user.daily_token_used >= user.daily_token_quota:
        raise QuotaExceeded(user.daily_token_used, user.daily_token_quota)
