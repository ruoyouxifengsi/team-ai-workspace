def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_list_update_delete(client, member_token):
    r = client.post("/api/chat/conversations", headers=_auth(member_token), json={})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    r = client.get("/api/chat/conversations", headers=_auth(member_token))
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())

    r = client.put(f"/api/chat/conversations/{cid}",
                   headers=_auth(member_token), json={"title": "renamed"})
    assert r.status_code == 200
    assert r.json()["title"] == "renamed"

    r = client.delete(f"/api/chat/conversations/{cid}", headers=_auth(member_token))
    assert r.status_code == 204

    r = client.get("/api/chat/conversations", headers=_auth(member_token))
    assert all(c["id"] != cid for c in r.json())


def test_other_user_cannot_access(client, admin_token, member_token):
    r = client.post("/api/chat/conversations", headers=_auth(member_token), json={})
    cid = r.json()["id"]

    r = client.get(f"/api/chat/conversations/{cid}/messages",
                   headers=_auth(admin_token))
    assert r.status_code == 404


def test_list_messages_empty(client, member_token):
    r = client.post("/api/chat/conversations", headers=_auth(member_token), json={})
    cid = r.json()["id"]
    r = client.get(f"/api/chat/conversations/{cid}/messages",
                   headers=_auth(member_token))
    assert r.status_code == 200
    assert r.json() == []


def test_send_invokes_agent_and_returns_assistant_reply(client, member_token, monkeypatch):
    from app.llm.base import LLMResponse

    class _Stub:
        def chat(self, messages, tools=None, temperature=0.7):
            return LLMResponse(content="echo: " + messages[-1]["content"],
                               tool_calls=[], tokens_in=1, tokens_out=1,
                               finish_reason="stop")

    monkeypatch.setattr(
        "app.agent.loop.make_client_for_user",
        lambda u, s: (_Stub(), False),
    )

    r = client.post("/api/chat/conversations",
                    headers=_auth(member_token), json={})
    cid = r.json()["id"]
    r = client.post(
        f"/api/chat/conversations/{cid}/send",
        headers=_auth(member_token), json={"content": "hello"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"assistant_content": "echo: hello"}

    r = client.get(f"/api/chat/conversations/{cid}/messages",
                   headers=_auth(member_token))
    msgs = r.json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]


def test_send_rejects_too_long_message(client, member_token):
    r = client.post("/api/chat/conversations",
                    headers=_auth(member_token), json={})
    cid = r.json()["id"]
    r = client.post(
        f"/api/chat/conversations/{cid}/send",
        headers=_auth(member_token), json={"content": "x" * 10001},
    )
    assert r.status_code == 413


def test_send_returns_429_when_quota_exceeded(client, member_token, monkeypatch):
    from datetime import datetime

    from app.deps import _session_factory
    from app.models import User
    db = _session_factory()
    alice = db.query(User).filter_by(username="alice").one()
    alice.daily_token_used = alice.daily_token_quota
    alice.daily_token_reset_at = datetime.utcnow()
    db.commit()

    r = client.post("/api/chat/conversations",
                    headers=_auth(member_token), json={})
    cid = r.json()["id"]
    r = client.post(
        f"/api/chat/conversations/{cid}/send",
        headers=_auth(member_token), json={"content": "hi"},
    )
    assert r.status_code == 429
