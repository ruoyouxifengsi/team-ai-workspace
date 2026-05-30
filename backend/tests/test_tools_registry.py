import pytest

from app.tools import registry


@pytest.fixture(autouse=True)
def clean_registry():
    saved = dict(registry._TOOLS)
    registry._TOOLS.clear()
    yield
    registry._TOOLS.clear()
    registry._TOOLS.update(saved)


def test_register_and_execute():
    @registry.register_tool(
        name="echo",
        description="echo back",
        parameters={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
    )
    def _echo(x: str, **ctx) -> dict:
        return {"echoed": x, "ctx_keys": sorted(ctx.keys())}

    assert "echo" in registry._TOOLS
    schemas = registry.all_schemas()
    assert schemas[0]["function"]["name"] == "echo"
    result = registry.execute("echo", {"x": "hi"}, user_id=7)
    assert result == {"echoed": "hi", "ctx_keys": ["user_id"]}


def test_execute_unknown_tool_returns_error():
    assert registry.execute("missing", {}) == {"error": "unknown tool: missing"}


def test_execute_catches_exceptions():
    @registry.register_tool(
        name="boom", description="boom",
        parameters={"type": "object", "properties": {}},
    )
    def _boom(**ctx):
        raise RuntimeError("kaboom")
    out = registry.execute("boom", {})
    assert out == {"error": "kaboom"}
