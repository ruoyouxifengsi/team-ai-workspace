import pytest

from app.agent.loop import AgentMaxStepsExceeded, run_loop
from app.chat.service import create_conversation, list_messages
from app.config import get_settings
from app.llm.base import LLMResponse, ToolCall
from app.models import User
from app.quota.exceptions import QuotaExceeded


class _StubClient:
    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.calls: list[list[dict]] = []

    def chat(self, messages, tools=None, temperature=0.7):
        self.calls.append(messages)
        return self._responses.pop(0)


def _stub_factory(client):
    def _mk(user, settings):
        return client, False
    return _mk


def _alice():
    from app.deps import _session_factory
    db = _session_factory()
    return db, db.query(User).filter_by(username="alice").one()


def test_single_turn_no_tools(client, member_token, env, monkeypatch):
    db, user = _alice()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    stub = _StubClient([
        LLMResponse(content="hello back", tool_calls=[],
                    tokens_in=3, tokens_out=2, finish_reason="stop"),
    ])
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))

    out = run_loop(db, settings, user, conv, "hi")
    assert out == "hello back"

    msgs = list_messages(db, conv.id, user.id)
    assert [m.role for m in msgs] == ["user", "assistant"]
    db.refresh(user)
    assert user.daily_token_used == 5


def test_tool_call_then_final(client, member_token, env, monkeypatch):
    db, user = _alice()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    stub = _StubClient([
        LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="call_1", name="list_files",
                                  arguments={"area": "personal"})],
            tokens_in=10, tokens_out=4, finish_reason="tool_calls",
        ),
        LLMResponse(content="you have 0 files", tool_calls=[],
                    tokens_in=8, tokens_out=4, finish_reason="stop"),
    ])
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))
    out = run_loop(db, settings, user, conv, "list please")
    assert "0 files" in out

    msgs = list_messages(db, conv.id, user.id)
    roles = [m.role for m in msgs]
    assert roles == ["user", "assistant", "tool", "assistant"]


def test_max_steps_exceeded(client, member_token, env, monkeypatch):
    db, user = _alice()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    looping = LLMResponse(
        content=None,
        tool_calls=[ToolCall(id="c", name="list_files",
                              arguments={"area": "personal"})],
        tokens_in=1, tokens_out=1, finish_reason="tool_calls",
    )
    stub = _StubClient([looping] * 25)
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))
    with pytest.raises(AgentMaxStepsExceeded):
        run_loop(db, settings, user, conv, "loop")


def test_charges_tokens_on_max_steps_failure(client, member_token, env, monkeypatch):
    db, user = _alice()
    user.daily_token_used = 0
    db.commit()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    looping = LLMResponse(
        content=None,
        tool_calls=[ToolCall(id="c", name="list_files",
                              arguments={"area": "personal"})],
        tokens_in=3, tokens_out=2, finish_reason="tool_calls",
    )
    stub = _StubClient([looping] * 25)
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))
    import pytest as _pytest
    with _pytest.raises(AgentMaxStepsExceeded):
        run_loop(db, settings, user, conv, "loop")
    db.refresh(user)
    # 20 steps × 5 tokens each = 100
    assert user.daily_token_used == 100


def test_quota_exceeded_blocks_call(client, member_token, env, monkeypatch):
    db, user = _alice()
    user.daily_token_used = user.daily_token_quota
    # Ensure check_and_reset does NOT reset within today's window
    from datetime import datetime
    user.daily_token_reset_at = datetime.utcnow()
    db.commit()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    stub = _StubClient([])
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))
    with pytest.raises(QuotaExceeded):
        run_loop(db, settings, user, conv, "hi")


def test_context_too_long_raises(client, member_token, env, monkeypatch):
    db, user = _alice()
    settings = get_settings()
    conv = create_conversation(db, user.id, "t")
    big = "x" * (250_000)  # > 60k tokens at 4-char/token
    stub = _StubClient([
        LLMResponse(content="ok", tool_calls=[],
                    tokens_in=1, tokens_out=1, finish_reason="stop"),
    ])
    monkeypatch.setattr("app.agent.loop.make_client_for_user", _stub_factory(stub))
    from app.agent.loop import ContextTooLong
    with pytest.raises(ContextTooLong):
        run_loop(db, settings, user, conv, big)
