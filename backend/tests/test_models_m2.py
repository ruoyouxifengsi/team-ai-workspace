from datetime import datetime

from app.models import Conversation, Feedback, Message, User


def test_user_has_new_m2_fields(db_session):
    u = User(username="x", password_hash="h", role="member")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    assert u.personal_deepseek_key_enc is None
    assert u.daily_token_quota == 1_000_000


def test_conversation_fields():
    c = Conversation(user_id=1, title="new")
    assert c.title == "new"
    assert c.user_id == 1


def test_message_fields():
    m = Message(
        conversation_id=1, role="assistant", content="hi",
        tool_name=None, tool_args=None, tool_result=None, tool_call_id=None,
        tokens_in=10, tokens_out=5,
    )
    assert m.role == "assistant"
    assert m.tokens_in == 10


def test_feedback_fields():
    f = Feedback(user_id=1, conversation_id=2, text="bug")
    assert f.text == "bug"
    assert f.created_at is None or isinstance(f.created_at, datetime)
