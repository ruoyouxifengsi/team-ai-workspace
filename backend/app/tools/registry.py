from collections.abc import Callable
from typing import Any

_TOOLS: dict[str, dict[str, Any]] = {}


def register_tool(*, name: str, description: str, parameters: dict) -> Callable:
    def deco(fn: Callable) -> Callable:
        _TOOLS[name] = {
            "fn": fn,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return fn
    return deco


def all_schemas() -> list[dict]:
    return [t["schema"] for t in _TOOLS.values()]


def execute(name: str, args: dict, **ctx) -> dict:
    if name not in _TOOLS:
        return {"error": f"unknown tool: {name}"}
    try:
        return _TOOLS[name]["fn"](**args, **ctx)
    except Exception as e:
        return {"error": str(e)}
