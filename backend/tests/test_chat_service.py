import json

import pytest

from app.chat.service import (
    build_context,
    create_conversation,
    delete_conversation,
    list_conversations,
    list_messages,
    persist_message,
    update_title,
)
from app.config import get_settings  # noqa: F401
from app.llm.base import ToolCall
from app.models import Conversation, User  # noqa: F401


def _alice():
    from app.deps import _session_factory
    db = _session_factory()
    return db, db.query(User).filter_by(username="alice").one()


def test_create_and_list(client, member_token, env):
    db, user = _alice()
    c = create_conversation(db, user.id, "first")
    assert c.id is not None
    rows = list_conversations(db, user.id)
    assert rows[0].id == c.id


def test_update_title(client, member_token, env):
    db, user = _alice()
    c = create_conversation(db, user.id, "old")
    update_title(db, c.id, user.id, "new")
    db.refresh(c)
    assert c.title == "new"


def test_delete_cascades(client, member_token, env):
    db, user = _alice()
    c = create_conversation(db, user.id, "x")
    persist_message(db, c, role="user", content="hi")
    assert delete_conversation(db, c.id, user.id) is True
    assert list_messages(db, c.id, user.id) == []


def test_other_user_cannot_delete(client, admin_token, member_token, env):
    db, alice = _alice()
    c = create_conversation(db, alice.id, "x")
    admin = db.query(User).filter_by(username="admin").one()
    with pytest.raises(PermissionError):
        delete_conversation(db, c.id, admin.id)


def test_persist_and_build_context_round_trip(client, member_token, env):
    db, user = _alice()
    c = create_conversation(db, user.id, "ctx")
    persist_message(db, c, role="user", content="list please")
    persist_message(
        db, c, role="assistant", content=None,
        tool_calls=[ToolCall(id="call_1", name="list_files",
                              arguments={"area": "personal"})],
        tokens_in=10, tokens_out=2,
    )
    persist_message(
        db, c, role="tool", tool_name="list_files", tool_call_id="call_1",
        tool_result={"ok": True},
    )
    persist_message(db, c, role="assistant", content="done",
                    tokens_in=5, tokens_out=2)

    msgs = build_context(db, c)
    assert msgs[0]["role"] == "system"
    assert msgs[1] == {"role": "user", "content": "list please"}
    assert msgs[2]["role"] == "assistant"
    assert msgs[2]["tool_calls"][0]["function"]["name"] == "list_files"
    assert json.loads(msgs[2]["tool_calls"][0]["function"]["arguments"]) == {"area": "personal"}
    assert msgs[3] == {"role": "tool", "tool_call_id": "call_1",
                       "content": json.dumps({"ok": True}, ensure_ascii=False)}
    assert msgs[4] == {"role": "assistant", "content": "done"}
