import json

import httpx
import pytest

from app.llm.deepseek import DeepSeekClient


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def test_chat_returns_plain_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer sk-team"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-chat"
        assert body["messages"] == [{"role": "user", "content": "hi"}]
        return httpx.Response(200, json={
            "choices": [{
                "message": {"role": "assistant", "content": "hello"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        })

    client = DeepSeekClient(
        api_key="sk-team",
        base_url="https://api.deepseek.com",
        transport=_mock_transport(handler),
    )
    r = client.chat([{"role": "user", "content": "hi"}])
    assert r.content == "hello"
    assert r.tool_calls == []
    assert r.tokens_in == 3
    assert r.tokens_out == 2
    assert r.finish_reason == "stop"


def test_chat_parses_tool_calls():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_42",
                        "type": "function",
                        "function": {"name": "list_files",
                                     "arguments": '{"area": "personal"}'},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 8},
        })

    client = DeepSeekClient(
        api_key="sk-x", base_url="https://api.deepseek.com",
        transport=_mock_transport(handler),
    )
    r = client.chat(
        [{"role": "user", "content": "list"}],
        tools=[{"type": "function", "function": {"name": "list_files"}}],
    )
    assert r.content is None
    assert len(r.tool_calls) == 1
    assert r.tool_calls[0].id == "call_42"
    assert r.tool_calls[0].name == "list_files"
    assert r.tool_calls[0].arguments == {"area": "personal"}
    assert r.finish_reason == "tool_calls"


def test_chat_raises_on_4xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad key"})
    client = DeepSeekClient(
        api_key="sk-bad", base_url="https://api.deepseek.com",
        transport=_mock_transport(handler),
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.chat([{"role": "user", "content": "x"}])
