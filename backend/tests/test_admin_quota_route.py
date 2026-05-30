def _auth(t): return {"Authorization": f"Bearer {t}"}


def test_admin_can_update_quota(client, admin_token, member_token):
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    alice = db.query(User).filter_by(username="alice").one()

    r = client.put(
        f"/api/admin/users/{alice.id}/quota",
        headers=_auth(admin_token), json={"daily_token_quota": 5_000_000},
    )
    assert r.status_code == 200
    db.refresh(alice)
    assert alice.daily_token_quota == 5_000_000


def test_member_cannot_update_quota(client, admin_token, member_token):
    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    alice = db.query(User).filter_by(username="alice").one()
    r = client.put(
        f"/api/admin/users/{alice.id}/quota",
        headers=_auth(member_token), json={"daily_token_quota": 1},
    )
    assert r.status_code == 403


def test_unknown_user_404(client, admin_token):
    r = client.put(
        "/api/admin/users/9999/quota",
        headers=_auth(admin_token), json={"daily_token_quota": 1},
    )
    assert r.status_code == 404
