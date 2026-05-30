from app.llm.base import LLMResponse, ToolCall


def test_toolcall_dataclass():
    tc = ToolCall(id="call_1", name="read_text", arguments={"file_id": 5})
    assert tc.id == "call_1"
    assert tc.name == "read_text"
    assert tc.arguments == {"file_id": 5}


def test_llmresponse_dataclass():
    r = LLMResponse(content="hi", tool_calls=[], tokens_in=10, tokens_out=2, finish_reason="stop")
    assert r.content == "hi"
    assert r.tool_calls == []
    assert r.finish_reason == "stop"
