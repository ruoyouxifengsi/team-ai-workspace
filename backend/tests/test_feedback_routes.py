def _auth(t): return {"Authorization": f"Bearer {t}"}


def test_member_can_submit_feedback(client, member_token):
    r = client.post("/api/feedback", headers=_auth(member_token),
                    json={"text": "AI 把方案改坏了", "conversation_id": None})
    assert r.status_code == 201
    assert r.json()["text"] == "AI 把方案改坏了"


def test_admin_lists_feedback(client, admin_token, member_token):
    client.post("/api/feedback", headers=_auth(member_token),
                json={"text": "first", "conversation_id": None})
    client.post("/api/feedback", headers=_auth(member_token),
                json={"text": "second", "conversation_id": None})
    r = client.get("/api/admin/feedback", headers=_auth(admin_token))
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 2
    assert {"text", "user_id", "conversation_id", "created_at"}.issubset(items[0].keys())


def test_member_cannot_list(client, member_token):
    r = client.get("/api/admin/feedback", headers=_auth(member_token))
    assert r.status_code == 403
