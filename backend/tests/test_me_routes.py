def _auth(t): return {"Authorization": f"Bearer {t}"}


def test_get_settings_initial(client, member_token):
    r = client.get("/api/me/settings", headers=_auth(member_token))
    assert r.status_code == 200
    body = r.json()
    assert body["has_personal_key"] is False
    assert body["daily_token_used"] == 0
    assert body["daily_token_quota"] >= 1
    assert "key" not in body


def test_set_personal_key_then_get(client, member_token):
    r = client.put("/api/me/settings/key",
                   headers=_auth(member_token), json={"key": "sk-mine"})
    assert r.status_code == 204
    r = client.get("/api/me/settings", headers=_auth(member_token))
    assert r.json()["has_personal_key"] is True


def test_delete_personal_key(client, member_token):
    client.put("/api/me/settings/key",
               headers=_auth(member_token), json={"key": "sk-mine"})
    r = client.delete("/api/me/settings/key", headers=_auth(member_token))
    assert r.status_code == 204
    r = client.get("/api/me/settings", headers=_auth(member_token))
    assert r.json()["has_personal_key"] is False


def test_set_key_rejects_empty(client, member_token):
    r = client.put("/api/me/settings/key",
                   headers=_auth(member_token), json={"key": ""})
    assert r.status_code == 422
